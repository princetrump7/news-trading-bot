"""AI analysis engine — sends news to LLM and parses structured signals."""

import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, OPENAI_BASE_URL, OPENROUTER_REFERER, OPENROUTER_TITLE
from prompts import SYSTEM_PROMPT, USER_PROMPT

# Build the OpenAI client (works with OpenRouter, OpenAI, or any compatible endpoint)
extra_headers = {}
is_openrouter = "openrouter.ai" in (OPENAI_BASE_URL or "")

if is_openrouter:
    extra_headers = {
        "HTTP-Referer": OPENROUTER_REFERER,
        "X-Title": OPENROUTER_TITLE,
    }

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL or None,
    default_headers=extra_headers,
)


DEFAULT_SIGNAL = {
    "asset": "NONE",
    "ticker": "N/A",
    "bias": "neutral",
    "impact_score": 0,
    "confidence": 0,
    "reason": "Analysis failed or returned unparseable output.",
    "trade_idea": "ignore",
    "time_horizon": "medium",
}


def analyze_news(article: dict) -> dict:
    """Send article to LLM and return a parsed trading signal dict."""
    user_msg = USER_PROMPT.format(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        published=article.get("published", ""),
    )

    try:
        raw = _analyze_openai(user_msg)

        signal = _parse_signal(raw)
        signal["_raw_analysis"] = raw
        signal["_article_link"] = article.get("link", "")

        # If parsing failed, try once more with a stronger follow-up
        if signal.get("_error") and raw.strip():
            signal = _force_json(raw, article.get("link", ""))

        return signal

    except Exception as e:
        print(f"❌ LLM analysis error: {e}")
        return {**DEFAULT_SIGNAL, "_error": str(e), "_article_link": article.get("link", "")}


def _analyze_openai(user_msg: str) -> str:
    """Call LLM with system prompt + article. Returns raw response text."""
    try:
        # Try with response_format hint first (some models support it)
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
    except Exception:
        # Fallback: retry without response_format if model doesn't support it
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=600,
        )

    msg = response.choices[0].message

    # Standard content field
    if msg.content:
        return msg.content

    # Thinking/reasoning models put response in a reasoning field
    reasoning = getattr(msg, "reasoning", None)
    if reasoning:
        return reasoning

    # Check model_extra for reasoning (some providers use non-standard fields)
    if msg.model_extra:
        for key in ("reasoning", "reasoning_content", "thinking", "thinking_content"):
            val = msg.model_extra.get(key)
            if val:
                return str(val)

    # Last resort: dump the whole thing
    return str(msg) if msg else ""


# ---- JSON parsing ----

JSON_FIELDS = ["asset", "ticker", "bias", "impact_score", "confidence", "reason", "trade_idea", "time_horizon"]

BIAS_VALUES = {"bullish", "bearish", "neutral"}
TRADE_VALUES = {"buy", "sell", "ignore"}
ASSET_VALUES = {"xauusd", "stocks", "both", "none"}
HORIZON_VALUES = {"short", "medium", "long"}


def _parse_signal(raw: str) -> dict:
    """Try to parse JSON from LLM response. Returns signal dict or DEFAULT_SIGNAL."""
    if not raw:
        return {**DEFAULT_SIGNAL, "reason": "Empty response from LLM."}

    # Strip markdown fences
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Try to find JSON object
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not json_match:
        # Failed — send back what we got for _force_json fallback
        return {**DEFAULT_SIGNAL, "_raw": raw}

    data = _safe_json_parse(json_match.group())
    if data is None:
        return {**DEFAULT_SIGNAL, "_raw": raw}

    return _build_signal(data, raw)


def _safe_json_parse(text: str) -> dict | None:
    """Parse JSON with extra resilience for trailing commas, single quotes, etc."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try fixing common issues: single quotes → double quotes
    try:
        fixed = re.sub(r"(?<!\\)'(?!=)|\"(?=:)|(?<=: )\"", '"', text)
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Try fixing unquoted keys
    try:
        fixed = re.sub(r'(\w+)(?=\s*:)', r'"\1"', text)
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    return None


def _build_signal(data: dict, raw: str) -> dict:
    """Build validated signal dict from parsed JSON data."""
    # Normalize string fields
    asset = str(data.get("asset", DEFAULT_SIGNAL["asset"])).upper()
    if asset.lower() not in ASSET_VALUES:
        asset = DEFAULT_SIGNAL["asset"]

    ticker = str(data.get("ticker", DEFAULT_SIGNAL["ticker"])).upper()
    bias = str(data.get("bias", DEFAULT_SIGNAL["bias"])).lower()
    trade = str(data.get("trade_idea", DEFAULT_SIGNAL["trade_idea"])).lower()
    horizon = str(data.get("time_horizon", DEFAULT_SIGNAL["time_horizon"])).lower()

    if bias not in BIAS_VALUES:
        bias = DEFAULT_SIGNAL["bias"]
    if trade not in TRADE_VALUES:
        trade = DEFAULT_SIGNAL["trade_idea"]
    if horizon not in HORIZON_VALUES:
        horizon = DEFAULT_SIGNAL["time_horizon"]

    signal = {
        "asset": asset,
        "ticker": ticker if ticker != "N/A" else ("XAUUSD" if asset == "XAUUSD" else ticker),
        "bias": bias,
        "impact_score": max(0, min(100, int(data.get("impact_score", 0)))),
        "confidence": max(0, min(100, int(data.get("confidence", 0)))),
        "reason": str(data.get("reason", DEFAULT_SIGNAL["reason"])),
        "trade_idea": trade,
        "time_horizon": horizon,
    }
    return signal


def _force_json(raw: str, article_link: str) -> dict:
    """Fallback: try to extract fields from free text when JSON parsing failed."""
    lower = raw.lower()
    extracted = {}

    # Detect asset from text
    if any(w in lower for w in ["gold", "xau", "xauusd", "bullion"]):
        extracted["asset"] = "XAUUSD"
        extracted["ticker"] = "XAUUSD"
    elif any(w in lower for w in ["stock", "equity", "nasdaq", "s&p"]):
        extracted["asset"] = "STOCKS"
        extracted["ticker"] = "SPY"

    # Detect bias from text
    if any(w in lower for w in ["bullish", "positive", "rally", "increase", "gain"]):
        extracted["bias"] = "bullish"
        extracted["trade_idea"] = "buy"
    elif any(w in lower for w in ["bearish", "negative", "decline", "drop", "sell-off", "decrease", "loss"]):
        extracted["bias"] = "bearish"
        extracted["trade_idea"] = "sell"
    else:
        extracted["bias"] = "neutral"
        extracted["trade_idea"] = "ignore"

    # Extract ticker via uppercase patterns
    tickers = re.findall(r'\b([A-Z]{2,5})\b', raw)
    known_tickers = {"AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META",
                     "SPY", "QQQ", "DIA", "XAUUSD", "GOLD"}
    found = [t for t in tickers if t in known_tickers]
    if found:
        extracted["ticker"] = found[0]

    signal = _build_signal({**DEFAULT_SIGNAL, **extracted}, raw)
    signal["_raw_analysis"] = raw
    signal["_article_link"] = article_link
    signal["_from_fallback"] = True
    return signal
