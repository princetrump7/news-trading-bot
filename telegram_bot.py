"""Telegram bot — sends formatted trading signals to a chat."""

import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Initialize bot once (module level)
bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

# Persistent event loop to avoid RuntimeError('Event loop is closed') on repeated calls
_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def send_signal(text: str) -> bool:
    """Send a message to the configured Telegram chat. Returns True on success."""
    if not bot:
        print("❌ Telegram bot not initialized — missing token.")
        return False
    if not TELEGRAM_CHAT_ID:
        print("❌ No TELEGRAM_CHAT_ID configured.")
        return False

    try:
        loop = _get_loop()
        loop.run_until_complete(
            asyncio.wait_for(
                bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=15,
                ),
                timeout=30,
            )
        )
        return True
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False


def format_signal(article: dict, signal: dict) -> str:
    """Format an article + signal dict into a Telegram message string."""
    asset = signal.get("asset", "NONE")
    bias = signal.get("bias", "neutral")
    confidence = signal.get("confidence", 0)
    impact = signal.get("impact_score", 0)
    trade = signal.get("trade_idea", "ignore")

    # Emoji header based on bias
    if bias == "bullish":
        header = "🟢 BULLISH"
    elif bias == "bearish":
        header = "🔴 BEARISH"
    else:
        header = "⚪ NEUTRAL"

    # Asset emoji
    asset_emoji = {"XAUUSD": "🥇", "STOCKS": "📈", "BOTH": "🌐", "NONE": "💬"}

    # Confidence bar
    conf_bar = "▓" * (confidence // 20) + "░" * (5 - confidence // 20)

    trade_emoji = {"buy": "✅", "sell": "❌", "ignore": "⏭️"}

    # Build ticker display
    ticker = signal.get("ticker", "N/A")
    ticker_display = f"*{ticker}*" if ticker and ticker != "N/A" else f"*{asset}*"

    msg = (
        f"🚨 *NEWS SIGNAL*\n"
        f"{'─' * 32}\n"
        f"\n"
        f"*{article.get('title', 'Untitled')}*\n"
        f"\n"
        f"┌ {'─' * 28} ┐\n"
        f"  {asset_emoji.get(asset, '📰')} {header} on {ticker_display}\n"
        f"  📊 Impact: {impact}/100  |  Confidence: {conf_bar} {confidence}%\n"
        f"  🎯 Trade: {trade_emoji.get(trade, '➡️')} *{trade.upper()}*\n"
        f"  ⏱ Horizon: *{signal.get('time_horizon', 'medium')}*\n"
        f"└ {'─' * 28} ┘\n"
        f"\n"
        f"💡 *Reason:*\n{signal.get('reason', 'N/A')}\n"
    )

    # Add TP/SL block if present (only for actionable signals)
    entry = signal.get("entry_zone")
    tp = signal.get("take_profit")
    sl = signal.get("stop_loss")

    if trade != "ignore" and (entry or tp or sl):
        msg += f"\n┌ {'─' * 28} ┐\n"
        if entry:
            msg += f"  📌 *Entry:* {entry}\n"
        if tp:
            msg += f"  🎯 *TP:* {tp}\n"
        if sl:
            msg += f"  🛑 *SL:* {sl}\n"
        msg += f"└ {'─' * 28} ┘\n"

    msg += (
        f"\n"
        f"🔗 [Read article]({signal.get('_article_link', article.get('link', ''))})\n"
        f"📅 {article.get('published', 'Unknown date')}"
    )

    return msg
