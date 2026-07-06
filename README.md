# AI News Trading Telegram Bot — MVP

Real-time financial news → AI analysis → trading signals → Telegram alerts.

Targets: **Gold (XAUUSD)** and **US Stocks**.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your keys
cp .env.example .env
# Edit .env with your Telegram bot token, chat ID, and OpenRouter key

# 3. Run
python app.py
```

## Configuration

| Env Var | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | (required) | Your Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | (required) | Your chat ID (use @userinfobot) |
| `OPENAI_API_KEY` | (required) | API key (OpenAI, OpenRouter, or compatible) |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL |
| `LLM_MODEL` | `openrouter/free` | Model name. Set to any model ID |
| `POLL_INTERVAL_SECONDS` | `20` | Seconds between RSS polls |
| `MAX_ARTICLES_PER_CYCLE` | `5` | Max articles to analyze per cycle (cost control) |
| `POLL_INTERVAL_SECONDS` | `20` | Seconds between RSS polls |
| `MAX_ARTICLES_PER_CYCLE` | `5` | Max articles to analyze per cycle (cost control) |

## How It Works

1. **Poll** — RSS feeds every N seconds (Yahoo Finance, CNBC, MarketWatch, Investing.com)
2. **Filter** — keyword match for gold, stocks, macro (Fed, CPI, rates, etc.)
3. **Analyze** — LLM returns structured JSON: asset, bias, confidence, trade idea
4. **Alert** — Formatted Telegram message with emoji indicators

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main loop — orchestrates everything |
| `config.py` | Env vars, RSS feed list, validation |
| `news_fetcher.py` | RSS ingestion with retry logic |
| `filter.py` | Gold/stocks/macro keyword filter |
| `analyzer.py` | LLM analysis with JSON parsing |
| `telegram_bot.py` | Telegram sender + message formatting |
| `prompts.py` | LLM prompt templates |

## Cost Notes

**With OpenRouter free models:** $0 — completely free, no rate limit concerns for this use case.
**With paid API:** each analysis costs ~$0.001–0.005. At 5 articles/cycle, 20s interval → ~900 analyses/day → ~$1–5/day.

Set `LLM_MODEL=openrouter/free` for $0 cost. Set `MAX_ARTICLES_PER_CYCLE=1` for minimum usage.
