"""Configuration — loads from .env or environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Required ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- API endpoint (OpenAI-compatible) ---
# OpenRouter:    https://openrouter.ai/api/v1
# OpenAI:        https://api.openai.com/v1
# Leave empty to use the default OpenAI endpoint.
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# OpenRouter requires these headers for identification
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "https://github.com/princ/news-trading-bot")
OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE", "News Trading Bot")

# --- Optional overrides ---
# "openrouter/free" = best available free model on OpenRouter
# "meta-llama/llama-3.3-70b-instruct:free" = reliable JSON output (recommended)
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "20"))
MAX_ARTICLES_PER_CYCLE = int(os.getenv("MAX_ARTICLES_PER_CYCLE", "5"))

# --- Sanity check ---
def validate():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        print(f"❌ Missing required env vars: {', '.join(missing)}")
        print(f"   Copy .env.example → .env and fill in your keys.")
        return False
    return True

# --- RSS feed list ---
RSS_FEEDS = [
    # Yahoo Finance — top financial headlines
    "https://feeds.finance.yahoo.com/rss/2.0/headline",
    # CNBC — market & business news
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    # MarketWatch — top stories
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    # Investing.com — latest news
    # (Using a common free RSS gateway; adjust if needed)
    "https://www.investing.com/rss/news.rss",
]
