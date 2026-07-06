"""AI analysis engine — sends news to LLM and parses structured signals."""

import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, OPENAI_BASE_URL, OPENROUTER_REFERER, OPENROUTER_TITLE
from prompts import ANALYZE_NEWS_PROMPT

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
    prompt = ANALYZE_NEWS_PROMPT.format(
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        published=article.get("published", ""),
    )

    try:
        raw = _analyze_openai(prompt)

        signal = _parse_signal(raw)
        signal["_raw_analysis"] = raw
        signal["_article_link"] = article.get("link", "")
        return signal

    except Exception as e:
        print(f"❌ LLM analysis error: {e}")
        return {**DEFAULT_SIGNAL, "_error": str(e), "_article_link": article.get("link", "")}


def _analyze_openai(prompt: str) -> str:
    """Call OpenAI and return raw text response."""
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def _parse_signal(raw: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and stray text."""
    if not raw:
        return {**DEFAULT_SIGNAL, "reason": "Empty response from LLM."}

    # Strip markdown code fences if present
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # Try to find JSON object in the response
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not json_match:
        return {**DEFAULT_SIGNAL, "reason": f"No JSON found in LLM response. Raw: {raw[:200]}"}

    try:
        data = json.loads(json_match.group())

        # Validate required fields with defaults
        signal = {
            "asset": str(data.get("asset", DEFAULT_SIGNAL["asset"])),
            "ticker": str(data.get("ticker", DEFAULT_SIGNAL["ticker"])),
            "bias": str(data.get("bias", DEFAULT_SIGNAL["bias"])),
            "impact_score": int(data.get("impact_score", 0)),
            "confidence": int(data.get("confidence", 0)),
            "reason": str(data.get("reason", DEFAULT_SIGNAL["reason"])),
            "trade_idea": str(data.get("trade_idea", DEFAULT_SIGNAL["trade_idea"])),
            "time_horizon": str(data.get("time_horizon", DEFAULT_SIGNAL["time_horizon"])),
        }

        # Clamp numeric fields
        signal["impact_score"] = max(0, min(100, signal["impact_score"]))
        signal["confidence"] = max(0, min(100, signal["confidence"]))

        return signal

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return {**DEFAULT_SIGNAL, "reason": f"JSON parse error: {e}. Raw: {raw[:200]}"}
