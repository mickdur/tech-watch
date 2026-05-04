import socket
import time
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
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
    socket.setdefaulttimeout(REQUEST_TIMEOUT)
    feed = feedparser.parse(url, request_headers=HEADERS)
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
    logger.info("Fetching Papers With Code API")
    try:
        resp = requests.get(
            "https://paperswithcode.com/api/v1/papers/?ordering=-arxiv_first_version&items_per_page=20",
            headers={**HEADERS, "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        cutoff = _cutoff()
        items = []
        for paper in data.get("results", []):
            published_str = paper.get("published") or paper.get("date_updated") or ""
            pub = None
            if published_str:
                try:
                    pub = datetime.fromisoformat(published_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                except Exception:
                    pass
            if pub and pub < cutoff:
                continue
            title = paper.get("title", "").strip()
            arxiv_id = paper.get("arxiv_id", "")
            url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else f"https://paperswithcode.com/paper/{paper.get('id', '')}"
            excerpt = paper.get("abstract", "")[:300]
            items.append(Item(title=title, url=url, source="Papers With Code", published=pub, excerpt=excerpt))
        logger.info("  -> %d items from Papers With Code", len(items))
        return items
    except Exception as exc:
        logger.error("FAILED Papers With Code: %s", exc)
        return []


def fetch_reddit_ml() -> list[Item]:
    logger.info("Fetching Reddit r/MachineLearning (RSS)")
    try:
        socket.setdefaulttimeout(REQUEST_TIMEOUT)
        feed = feedparser.parse(
            "https://www.reddit.com/r/MachineLearning/hot.rss?limit=25",
            request_headers=HEADERS,
        )
        cutoff = _cutoff()
        items = []
        for entry in feed.entries:
            pub = _parse_rss_date(entry)
            if pub and pub < cutoff:
                continue
            title = entry.get("title", "").strip()
            url = entry.get("link", "")
            excerpt = _excerpt(entry)
            items.append(Item(
                title=title,
                url=url,
                source="Reddit r/MachineLearning",
                published=pub,
                excerpt=excerpt,
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
