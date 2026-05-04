import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent.parent / "state" / "seen_urls.json"
RETENTION_DAYS = 7


def load_seen_urls() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    with open(STATE_FILE) as f:
        data = json.load(f)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    seen = {url for url, ts in data.items() if ts >= cutoff}
    logger.info("Loaded %d seen URLs from state", len(seen))
    return seen


def save_seen_urls(new_urls: list[str]) -> None:
    existing: dict[str, str] = {}
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            existing = json.load(f)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    existing = {url: ts for url, ts in existing.items() if ts >= cutoff}
    now = datetime.now(timezone.utc).isoformat()
    for url in new_urls:
        existing[url] = now
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(existing, f, indent=2, sort_keys=True)
    logger.info("Saved %d URLs to state (%d new)", len(existing), len(new_urls))
