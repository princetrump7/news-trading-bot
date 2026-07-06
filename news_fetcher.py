"""RSS news ingestion — polls multiple feeds and returns articles."""

import time
import feedparser
from config import RSS_FEEDS

def fetch_news(max_per_feed: int = 10) -> list[dict]:
    """Poll all configured RSS feeds. Returns a list of article dicts."""
    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for i, entry in enumerate(feed.entries):
                if i >= max_per_feed:
                    break

                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": url,
                })
        except Exception as e:
            print(f"⚠ RSS error for {url}: {e}")

    # Deduplicate by link
    seen = set()
    unique = []
    for a in articles:
        if a["link"] and a["link"] not in seen:
            seen.add(a["link"])
            unique.append(a)

    return unique

def fetch_news_with_retry(max_per_feed: int = 10, retries: int = 2) -> list[dict]:
    """Fetch news with simple retry logic."""
    for attempt in range(retries):
        articles = fetch_news(max_per_feed)
        if articles:
            return articles
        if attempt < retries - 1:
            print(f"⏳ No articles found, retrying... ({attempt + 1}/{retries})")
            time.sleep(2)
    return []
