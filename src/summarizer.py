import logging
import os
from datetime import datetime, timezone

import anthropic

from src.fetcher import Item

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2000

SYSTEM_PROMPT = (
    "You are a senior AI researcher writing a twice-daily digest for a technical audience "
    "interested in LLMs, generative AI, agents, dev tooling, and AI-powered productivity. "
    "Be precise, opinionated when warranted, and avoid filler. Always include source links."
)

OUTPUT_INSTRUCTIONS = """
Produce the digest using EXACTLY this structure. Replace the slot header based on the RUN_SLOT:
- morning:   **[MORNING DIGEST — {date}, 08:30]**
- afternoon: **[AFTERNOON DIGEST — {date}, 14:00]**

Then sections (omit any section with no relevant items):

**PAPERS & RESEARCH**
- [Title] — one sentence on what it does and why it matters. [Source](url)

**MODELS & RELEASES**
- [Title] — one sentence. [Source](url)

**AGENTS & AUTOMATION**
- [Title] — one sentence. [Source](url)

**DEV TOOLS & PRODUCTIVITY**
- [Title] — one sentence. [Source](url)

**FROM THE COMMUNITY** (Reddit, HN)
- [Title] — one sentence on why it's worth reading. [Source](url)

**EDITOR'S NOTE**
2–3 sentences: what's the signal in today's batch? Any emerging pattern or notable absence?

Rules:
- Do not invent content. Only use items from the provided list.
- If fewer than 3 items total are provided, output exactly: "No significant updates in this cycle."
- Do not add sections not listed above.
- Every bullet must end with a markdown link: [Source](url)
"""


def _format_items(items: list[Item]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        pub = item.published.strftime("%Y-%m-%d %H:%M UTC") if item.published else "unknown date"
        lines.append(
            f"{i}. [{item.source}] {item.title}\n"
            f"   URL: {item.url}\n"
            f"   Published: {pub}\n"
            f"   Excerpt: {item.excerpt or 'N/A'}"
        )
    return "\n\n".join(lines)


def summarize(items: list[Item], slot: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    date_str = datetime.now(timezone.utc).strftime("%d %b %Y").upper()
    instructions = OUTPUT_INSTRUCTIONS.format(date=date_str)

    if not items:
        logger.warning("No items to summarize — skipping API call")
        return "No significant updates in this cycle."

    user_content = (
        f"RUN_SLOT: {slot}\n\n"
        f"{instructions}\n\n"
        f"Here are the {len(items)} items to process:\n\n"
        f"{_format_items(items)}"
    )

    logger.info("Calling Claude API with %d items (slot=%s)", len(items), slot)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    digest = message.content[0].text.strip()
    logger.info(
        "Claude response: %d chars, stop_reason=%s",
        len(digest),
        message.stop_reason,
    )
    return digest
