"""
Configuration for the Crude Oil Signal Bot.
All secrets/settings come from environment variables so nothing sensitive
is ever committed to GitHub. On Railway, set these under Project > Variables.
"""

import os


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in your Railway project's Variables tab (or a local .env for testing)."
        )
    return value


# ---- Upstox API ----
# Access token is generated daily through Upstox's login/auth flow and expires
# at end of day. You MUST refresh this every trading day (see README for the
# auth steps) and update the Railway env var, or automate it with your own
# refresh flow.
UPSTOX_ACCESS_TOKEN = _get_env("UPSTOX_ACCESS_TOKEN", required=True)
UPSTOX_BASE_URL = "https://api.upstox.com"

# ---- Telegram ----
TELEGRAM_BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = _get_env("TELEGRAM_CHAT_ID", required=True)

# ---- Strategy parameters ----
EMA_FAST = int(_get_env("EMA_FAST", "9"))
EMA_SLOW = int(_get_env("EMA_SLOW", "21"))
ATR_PERIOD = int(_get_env("ATR_PERIOD", "14"))
BREAKOUT_LOOKBACK = int(_get_env("BREAKOUT_LOOKBACK", "10"))  # candles for high/low breakout
CANDLE_INTERVAL_MINUTES = int(_get_env("CANDLE_INTERVAL_MINUTES", "5"))

# TP/SL as multiples of ATR
SL_ATR_MULT = float(_get_env("SL_ATR_MULT", "1.0"))
TP1_ATR_MULT = float(_get_env("TP1_ATR_MULT", "1.0"))
TP2_ATR_MULT = float(_get_env("TP2_ATR_MULT", "2.0"))

# Strike spacing for MCX Crude Oil (in Rs, standard is 50 or 100 depending on cycle)
STRIKE_STEP = int(_get_env("STRIKE_STEP", "50"))

# ---- Scheduling ----
CHECK_INTERVAL_SECONDS = int(_get_env("CHECK_INTERVAL_SECONDS", "300"))  # every 5 min
# Minimum gap between two signals firing the same direction, to avoid spamming
# repeated alerts while the same trend/breakout condition persists.
MIN_MINUTES_BETWEEN_SAME_SIGNAL = int(_get_env("MIN_MINUTES_BETWEEN_SAME_SIGNAL", "30"))

# Market hours (IST). MCX Crude Oil intraday session.
MARKET_OPEN_HOUR = int(_get_env("MARKET_OPEN_HOUR", "9"))
MARKET_OPEN_MINUTE = int(_get_env("MARKET_OPEN_MINUTE", "0"))
MARKET_CLOSE_HOUR = int(_get_env("MARKET_CLOSE_HOUR", "23"))
MARKET_CLOSE_MINUTE = int(_get_env("MARKET_CLOSE_MINUTE", "30"))

# Instrument lookup
MCX_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz"
CRUDE_OIL_FUTURES_NAME_HINT = "CRUDEOIL"  # used to filter the instrument master
