# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run a digest locally (requires env vars below)
python main.py --slot morning
python main.py --slot afternoon
```

Required environment variables:
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Linting

Use `ruff` for linting and formatting:

```bash
pip install ruff

ruff check .          # lint
ruff check . --fix    # auto-fix
ruff format .         # format
```

`ruff` is not in `requirements.txt` — install it separately as a dev tool.

## Before committing

Run both checks and fix any issues before every commit:

```bash
ruff check . --fix && ruff format .
```

There are no automated tests. If you add tests, run them here too.

## Architecture

The pipeline is a straight linear sequence orchestrated by `main.py`:

```
fetch_all() → filter_items() → summarize() → send_digest()
```

**`src/fetcher.py`** — Pulls from 9 RSS feeds (via `feedparser`) and 2 scrapers (Papers With Code via BeautifulSoup, Reddit via JSON API). All sources are gated to items published within the last 12 hours (`CUTOFF_HOURS = 12`). Returns a list of `Item` dataclasses. Per-source failures are caught and logged without aborting the run.

**`src/filter.py`** — Pure keyword filter against `title + excerpt`. Three lists: `DISCARD_KEYWORDS` (hard exclude), `PRIORITY_KEYWORDS` (agents, dev tools, coding assistants), `BROAD_KEYWORDS` (model releases, research, infra). No ML scoring — substring match only.

**`src/summarizer.py`** — Sends filtered items to `claude-sonnet-4-20250514` with a fixed system prompt and a strict output schema (6 named sections). The `slot` argument (`morning`/`afternoon`) controls the digest header timestamp. Fails hard (raises) if `ANTHROPIC_API_KEY` is missing or the API call errors.

**`src/telegram.py`** — Posts to Telegram bot. Splits messages at newline boundaries if over 4096 chars. Fails hard (`sys.exit(1)`) on any HTTP or network error.

## Scheduling

GitHub Actions (`tech-watch.yml`) runs on two cron schedules (UTC 06:30 and 12:00, approximating 08:30 and 14:00 Paris time). The slot (`morning`/`afternoon`) is derived from the UTC hour at runtime. Manual dispatch via `workflow_dispatch` input is also supported.

## Extending

- **Add RSS feed**: add a tuple to `sources` list in `fetch_rss_sources()`.
- **Add a scraper**: follow the pattern of `fetch_papers_with_code()` or `fetch_reddit_ml()`, then call from `fetch_all()`.
- **Adjust relevance**: edit `PRIORITY_KEYWORDS`, `BROAD_KEYWORDS`, or `DISCARD_KEYWORDS` in `filter.py`.
- **Change digest structure**: edit `OUTPUT_INSTRUCTIONS` in `summarizer.py` — the section names and format rules are in the prompt, not in code.
