#!/usr/bin/env python3
"""
AI News Trading Telegram Bot — MVP Main Loop.

Polls RSS feeds → keyword filters → LLM analysis → Telegram alert.
Runs a health HTTP server for Render deployment.
"""

import os
import time
import signal
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Fix Windows cp1252 encoding for emoji prints
if sys.stdout.encoding and sys.stdout.encoding.lower() in ('cp1252', 'ansi_x3.4-1968'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config import validate, POLL_INTERVAL_SECONDS, MAX_ARTICLES_PER_CYCLE
from news_fetcher import fetch_news_with_retry
from filter import is_relevant
from analyzer import analyze_news
from telegram_bot import send_signal, format_signal


# --- State ---
seen_links: set[str] = set()
running = True


# --- Health server (Render needs an HTTP listener) ---
PORT = int(os.getenv("PORT", "8000"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass  # quiet


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    while running:
        server.handle_request()


def handle_shutdown(sig, frame):
    """Graceful shutdown."""
    global running
    print("\n👋 Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def main():
    if not validate():
        sys.exit(1)

    global running

    # Start health HTTP server in background thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    print(
        f"🚀 AI News Trading Bot — MVP\n"
        f"   Health endpoint: http://0.0.0.0:{PORT}\n"
        f"   Poll interval: {POLL_INTERVAL_SECONDS}s\n"
        f"   Max articles/cycle: {MAX_ARTICLES_PER_CYCLE}\n"
        f"   Press Ctrl+C to stop.\n"
    )

    cycle_count = 0
    total_signals = 0

    while running:
        cycle_count += 1
        print(f"\n[{cycle_count}] 🔄 Polling news feeds...")

        articles = fetch_news_with_retry(max_per_feed=10)
        print(f"   📰 Got {len(articles)} total articles")

        # Filter to relevant + unseen
        relevant = [a for a in articles if a["link"] not in seen_links and is_relevant(a)]

        # Add to seen set
        for a in articles:
            seen_links.add(a["link"])

        # Trim seen set to prevent unbounded memory growth
        if len(seen_links) > 10000:
            seen_links.clear()

        if not relevant:
            print(f"   ⏭️  No new relevant articles (pooled {len(seen_links)} unique links)")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # Rate limit: only analyze N articles per cycle
        to_analyze = relevant[:MAX_ARTICLES_PER_CYCLE]

        print(f"   🔍 {len(to_analyze)} relevant article(s) — sending to LLM...")

        for i, article in enumerate(to_analyze, 1):
            if not running:
                break

            matched = article.get("_matched_keywords", [])
            print(f"   [{i}/{len(to_analyze)}] Analyzing: {article['title'][:80]}...")
            print(f"       Keywords: {matched[:5]}")

            signal_data = analyze_news(article)
            message = format_signal(article, signal_data)

            success = send_signal(message)
            if success:
                total_signals += 1
                print(f"       ✅ Signal sent to Telegram")
            else:
                print(f"       ❌ Failed to send Telegram message")

        if running:
            print(f"   💤 Sleeping {POLL_INTERVAL_SECONDS}s...")
            time.sleep(POLL_INTERVAL_SECONDS)

    # Summary on shutdown
    print(
        f"\n{'=' * 40}\n"
        f"📊 Session Summary\n"
        f"   Cycles run: {cycle_count}\n"
        f"   Unique articles seen: {len(seen_links)}\n"
        f"   Signals sent: {total_signals}\n"
        f"{'=' * 40}"
    )


if __name__ == "__main__":
    main()
