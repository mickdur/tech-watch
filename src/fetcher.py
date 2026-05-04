import time
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CUTOFF_HOURS = 12
REQUEST_TIMEOUT = 10
FETCH_DELAY = 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TechWatchBot/1.0; +https://github.com/techwatch)"
}


@dataclass
class Item:
    title: str
    url: str
    source: str
    published: Optional[datetime] = None
    excerpt: str = ""


def _cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)


def _parse_rss_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _excerpt(entry) -> str:
    for attr in ("summary", "description"):
        text = getattr(entry, attr, None)
        if text:
            soup = BeautifulSoup(text, "html.parser")
            plain = soup.get_text(" ", strip=True)
            return plain[:300]
    return ""


def _fetch_feed(name: str, url: str) -> list[Item]:
    logger.info("Fetching RSS: %s", name)
    feed = feedparser.parse(url, request_headers=HEADERS, timeout=REQUEST_TIMEOUT)
    cutoff = _cutoff()
    items = []
    for entry in feed.entries:
        pub = _parse_rss_date(entry)
        if pub and pub < cutoff:
            continue
        items.append(Item(
            title=entry.get("title", "").strip(),
            url=entry.get("link", ""),
            source=name,
            published=pub,
            excerpt=_excerpt(entry),
        ))
    logger.info("  -> %d items from %s", len(items), name)
    return items


def fetch_rss_sources() -> list[Item]:
    sources = [
        ("Towards Data Science", "https://towardsdatascience.com/feed"),
        ("Medium / LLM", "https://medium.com/feed/tag/llm"),
        ("Hacker News", "https://news.ycombinator.com/rss"),
        ("TechCrunch AI", "https://techcrunch.com/tag/artificial-intelligence/feed/"),
        ("arXiv cs.AI", "https://arxiv.org/rss/cs.AI"),
        ("HuggingFace Blog", "https://huggingface.co/blog/feed.xml"),
        ("The Batch (DeepLearning.AI)", "https://www.deeplearning.ai/the-batch/feed/"),
        ("Anthropic Blog", "https://www.anthropic.com/rss.xml"),
        ("Google DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
    ]
    all_items: list[Item] = []
    for name, url in sources:
        try:
            all_items.extend(_fetch_feed(name, url))
        except Exception as exc:
            logger.error("FAILED RSS %s: %s", name, exc)
        time.sleep(FETCH_DELAY)
    return all_items


def fetch_papers_with_code() -> list[Item]:
    logger.info("Fetching Papers With Code (homepage)")
    try:
        resp = requests.get(
            "https://paperswithcode.com",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for card in soup.select(".paper-card")[:20]:
            title_el = card.select_one("h1 a, h2 a, .item-heading a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"https://paperswithcode.com{href}"
            abstract_el = card.select_one(".item-strip-abstract, p")
            excerpt = abstract_el.get_text(" ", strip=True)[:300] if abstract_el else ""
            items.append(Item(title=title, url=url, source="Papers With Code", excerpt=excerpt))
        logger.info("  -> %d items from Papers With Code", len(items))
        return items
    except Exception as exc:
        logger.error("FAILED Papers With Code: %s", exc)
        return []


def fetch_reddit_ml() -> list[Item]:
    logger.info("Fetching Reddit r/MachineLearning")
    try:
        resp = requests.get(
            "https://www.reddit.com/r/MachineLearning/hot.json?limit=25",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        cutoff = _cutoff()
        items = []
        for post in data["data"]["children"]:
            p = post["data"]
            created = datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc)
            if created < cutoff:
                continue
            title = p.get("title", "").strip()
            permalink = p.get("permalink", "")
            url = f"https://www.reddit.com{permalink}"
            selftext = p.get("selftext", "")[:300]
            items.append(Item(
                title=title,
                url=url,
                source="Reddit r/MachineLearning",
                published=created,
                excerpt=selftext,
            ))
        logger.info("  -> %d items from Reddit r/MachineLearning", len(items))
        return items
    except Exception as exc:
        logger.error("FAILED Reddit r/MachineLearning: %s", exc)
        return []


def fetch_all() -> list[Item]:
    all_items: list[Item] = []
    all_items.extend(fetch_rss_sources())
    time.sleep(FETCH_DELAY)
    all_items.extend(fetch_papers_with_code())
    time.sleep(FETCH_DELAY)
    all_items.extend(fetch_reddit_ml())
    logger.info("Total items fetched: %d", len(all_items))
    return all_items
