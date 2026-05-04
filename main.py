#!/usr/bin/env python3
"""
Tech-watch pipeline orchestrator.

Usage:
    python main.py --slot morning
    python main.py --slot afternoon
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GenAI tech-watch pipeline")
    parser.add_argument(
        "--slot",
        choices=["morning", "afternoon"],
        required=True,
        help="Which digest slot to run (morning | afternoon)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    slot = args.slot
    logger.info("=== Tech-watch starting (slot=%s) ===", slot)

    # 1. Fetch all sources
    from src.fetcher import fetch_all
    items = fetch_all()

    # 2. Deduplicate against previously seen URLs
    from src.state import load_seen_urls, save_seen_urls
    seen = load_seen_urls()
    items = [i for i in items if i.url not in seen]
    logger.info("After dedup: %d items remaining", len(items))

    # 3. Filter to relevant topics
    from src.filter import filter_items
    relevant = filter_items(items)

    # 4. Summarize with Claude
    from src.summarizer import summarize
    try:
        digest = summarize(relevant, slot)
    except Exception as exc:
        logger.error("Summarization failed: %s", exc)
        sys.exit(1)

    logger.info("Digest preview (first 200 chars): %s", digest[:200])

    # 5. Send to Telegram
    from src.telegram import send_digest
    send_digest(digest)

    # 6. Persist seen URLs so items are not repeated in future runs
    save_seen_urls([i.url for i in items])

    logger.info("=== Tech-watch complete ===")


if __name__ == "__main__":
    main()
