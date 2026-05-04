# GenAI Tech Watch

A fully automated pipeline that monitors ~11 sources twice a day, filters for LLM/GenAI relevance, summarizes with Claude, and delivers a structured digest to a Telegram bot. Runs on GitHub Actions — no server required.

---

## What it does

1. **Fetches** content from RSS feeds (arXiv, HuggingFace, Anthropic, DeepMind, TechCrunch AI, HN, Medium, TDS, The Batch), Papers With Code, and Reddit r/MachineLearning.
2. **Filters** to items published in the last 12 hours, then keeps only those relevant to: AI agents, dev tooling, productivity, workflow automation, model releases, and research.
3. **Summarizes** the filtered batch via Claude (`claude-sonnet-4-20250514`), producing a structured digest with sections: Papers & Research, Models & Releases, Agents & Automation, Dev Tools & Productivity, From the Community, and an Editor's Note.
4. **Delivers** to a Telegram bot (splits messages if over 4096 chars).
5. **Runs** twice daily via GitHub Actions cron (~08:30 and ~14:00 Paris time).

---

## 1. Create the Telegram bot

### Step 1 — Create the bot via BotFather

1. Open Telegram and search for **@BotFather** (verified blue checkmark).
2. Send the command `/newbot`.
3. BotFather will ask for a **name** (display name, e.g. "My Tech Watch") — type it and send.
4. It will then ask for a **username** (must end in `bot`, e.g. `mytechwatch_bot`) — type it and send.
5. BotFather replies with your **bot token**, which looks like:
   ```
   5839201847:AAGtK9mRkQp-xYZ123abcDEF456ghiJKL789
   ```
   Copy and save this token — you'll add it as a GitHub secret.

### Step 2 — Start the bot conversation (required to get your chat_id)

1. In Telegram, search for your new bot by its username and open the chat.
2. Send any message (e.g. `/start` or just "hello") — this is required so the bot can message you.

### Step 3 — Get your chat_id

Open this URL in a browser (replace `YOUR_BOT_TOKEN` with your actual token):

```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

You'll see a JSON response. Look for `"chat":{"id":XXXXXXXXX}` — that number is your `chat_id`. Example:

```json
{
  "result": [{
    "message": {
      "chat": {
        "id": 123456789,
        "first_name": "Your Name",
        "type": "private"
      }
    }
  }]
}
```

If the result array is empty, go back to Telegram and send another message to your bot, then refresh the URL.

---

## 2. Add GitHub Actions secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions → New repository secret** and add these three secrets:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (from console.anthropic.com) |
| `TELEGRAM_BOT_TOKEN` | The token from BotFather (step 1 above) |
| `TELEGRAM_CHAT_ID` | Your numeric chat ID (step 3 above) |

The exact names matter — the workflow references them by name.

---

## 3. Run locally for testing

### Prerequisites

```bash
pip install -r requirements.txt
```

### Set environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="5839201847:AAG..."
export TELEGRAM_CHAT_ID="123456789"
```

On Windows (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:TELEGRAM_BOT_TOKEN = "5839201847:AAG..."
$env:TELEGRAM_CHAT_ID = "123456789"
```

### Run a digest

```bash
# Morning digest
python main.py --slot morning

# Afternoon digest
python main.py --slot afternoon
```

All logs go to stdout. A successful run ends with `=== Tech-watch complete ===`.

---

## 4. How to add or remove sources

### Add an RSS feed

Open [`src/fetcher.py`](src/fetcher.py) and add a tuple to the `sources` list inside `fetch_rss_sources()`:

```python
sources = [
    ...
    ("My New Source", "https://example.com/feed.xml"),
]
```

### Remove an RSS feed

Delete the corresponding tuple from the same `sources` list.

### Add a scraper

Add a new function following the pattern of `fetch_papers_with_code()` or `fetch_reddit_ml()`, then call it from `fetch_all()` at the bottom of the file.

### Adjust topic filters

Open [`src/filter.py`](src/filter.py) and edit `PRIORITY_KEYWORDS` (high-signal topics), `BROAD_KEYWORDS` (wider LLM/GenAI scope), or `DISCARD_KEYWORDS` (noise to drop). All matching is case-insensitive substring search against the item title + excerpt.

---

## Project structure

```
tech-watch/
├── .github/
│   └── workflows/
│       └── tech-watch.yml   # GitHub Actions schedule
├── src/
│   ├── fetcher.py           # All source fetching logic
│   ├── filter.py            # Topic relevance filtering
│   ├── summarizer.py        # Claude API call + prompt
│   └── telegram.py          # Telegram delivery
├── main.py                  # Pipeline orchestrator
├── requirements.txt
└── README.md
```

---

## Scheduling details

The workflow runs at two UTC times:

| Cron | UTC | Paris CET (winter) | Paris CEST (summer) |
|---|---|---|---|
| `30 6 * * *` | 06:30 | 07:30 | 08:30 |
| `0 12 * * *` | 12:00 | 13:00 | 14:00 |

This is a deliberate approximation — GitHub Actions cron does not support timezone-aware scheduling. The pipeline determines "morning" vs "afternoon" based on the UTC hour at runtime, so the correct header always appears in the digest.

You can also trigger the workflow manually from **Actions → Tech Watch Digest → Run workflow** and select the slot.
