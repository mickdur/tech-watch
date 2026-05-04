import logging
import os
import sys

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LEN = 4096


def _split_message(text: str) -> list[str]:
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]

    parts = []
    while text:
        if len(text) <= MAX_MESSAGE_LEN:
            parts.append(text)
            break
        # Split at last newline within the limit to avoid cutting mid-line
        split_at = text.rfind("\n", 0, MAX_MESSAGE_LEN)
        if split_at == -1:
            split_at = MAX_MESSAGE_LEN
        parts.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return parts


def send_digest(digest: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
    if not chat_id:
        logger.error("TELEGRAM_CHAT_ID environment variable not set")
        sys.exit(1)

    url = TELEGRAM_API.format(token=token)
    parts = _split_message(digest)
    logger.info("Sending digest in %d message(s) to Telegram", len(parts))

    for idx, part in enumerate(parts, 1):
        payload = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Part %d/%d sent (status %d)", idx, len(parts), resp.status_code)
        except requests.HTTPError as exc:
            logger.error(
                "Telegram API error on part %d: HTTP %s — %s",
                idx,
                exc.response.status_code,
                exc.response.text,
            )
            sys.exit(1)
        except requests.RequestException as exc:
            logger.error("Telegram request failed on part %d: %s", idx, exc)
            sys.exit(1)
