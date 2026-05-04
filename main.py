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

    # 2. Filter to relevant topics
    from src.filter import filter_items
    relevant = filter_items(items)

    # 3. Summarize with Claude
    from src.summarizer import summarize
    try:
        digest = summarize(relevant, slot)
    except Exception as exc:
        logger.error("Summarization failed: %s", exc)
        sys.exit(1)

    logger.info("Digest preview (first 200 chars): %s", digest[:200])

    # 4. Send to Telegram
    from src.telegram import send_digest
    send_digest(digest)

    logger.info("=== Tech-watch complete ===")


if __name__ == "__main__":
    main()
