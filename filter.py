"""Keyword filter — keeps only articles likely to impact stocks or gold prices."""

# Stock-specific tickers and earnings — high signal
STOCK_KEYWORDS = [
    "earnings", "nasdaq", "dow jones",
    "s&p 500", "s&p", "spy", "qqq", "equity", "equities",
    "aapl", "tsla", "nvda", "amzn", "msft", "meta", "googl", "goog",
    "rally", "sell-off", "correction", "bear market", "bull market",
    "volatility", "vix", "ipo", "buyback", "stock split",
]

# Macroeconomic — directly moves markets
MACRO_KEYWORDS = [
    "inflation", "cpi", "ppi", "fed", "federal reserve",
    "interest rate", "rate hike", "rate cut",
    "dollar index", "dxy", "treasury yield",
    "recession", "gdp", "jobs report", "nonfarm payrolls",
    "central bank", "monetary policy",
    "geopolitical", "sanctions", "tariff", "trade war",
    "safe haven", "risk off", "consumer spending",
]

# Commodities
GOLD_KEYWORDS = [
    "gold", "xauusd", "bullion", "precious metal",
]

# Company-level catalysts — high conviction
CATALYST_KEYWORDS = [
    "guidance", "forecast", "outperform", "downgrade", "upgrade",
    "merger", "acquisition", "antitrust", "regulatory",
    "layoffs", "restructuring", "ceo", "dividend",
    "profit", "revenue", "margin",
]

ALL_KEYWORDS = GOLD_KEYWORDS + MACRO_KEYWORDS + STOCK_KEYWORDS + CATALYST_KEYWORDS


def is_relevant(article: dict) -> bool:
    """Return True if the article mentions specific stock movers or macro drivers."""
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()

    match = any(k in text for k in ALL_KEYWORDS)
    if match:
        matched = [k for k in ALL_KEYWORDS if k in text]
        article["_matched_keywords"] = matched
    return match
