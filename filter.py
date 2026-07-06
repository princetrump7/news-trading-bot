"""Keyword filter — keeps only gold / stocks / macro articles."""

# Gold-related keywords
GOLD_KEYWORDS = [
    "gold", "xau", "xauusd", "goldman",
    "bullion", "precious metal", "silver",
]

# Macro keywords that move gold
MACRO_KEYWORDS = [
    "inflation", "cpi", "ppi", "fed", "federal reserve",
    "interest rate", "rate hike", "rate cut",
    "dollar", "dxy", "usd", "treasury yield",
    "recession", "gdp", "jobs report", "nonfarm",
    "central bank", "monetary policy",
    "geopolitical", "sanctions", "tariff",
    "safe haven", "risk off",
]

# Stock market keywords
STOCK_KEYWORDS = [
    "stock", "stocks", "earnings", "nasdaq", "dow jones",
    "s&p 500", "s&p", "spy", "qqq", "equity", "equities",
    "apple", "aapl", "tesla", "tsla", "microsoft", "msft",
    "nvidia", "nvda", "amazon", "amzn", "meta",
    "rally", "sell-off", "correction", "bear market", "bull market",
    "market", "bubble", "volatility", "vix",
]

ALL_KEYWORDS = GOLD_KEYWORDS + MACRO_KEYWORDS + STOCK_KEYWORDS


def is_relevant(article: dict) -> bool:
    """Return True if the article mentions gold, stocks, or major macro drivers."""
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()

    match = any(k in text for k in ALL_KEYWORDS)
    if match:
        # Find which keywords matched (for debugging)
        matched = [k for k in ALL_KEYWORDS if k in text]
        article["_matched_keywords"] = matched
    return match
