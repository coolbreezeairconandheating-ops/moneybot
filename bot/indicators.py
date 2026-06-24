"""
Plain-Python technical indicator calculations (no pandas/numpy dependency,
keeps the bot lightweight to deploy on Railway's free tier).

All functions expect candles as a list of dicts with keys:
    timestamp, open, high, low, close, volume
ordered OLDEST FIRST (chronological). Upstox returns newest-first, so the
caller is responsible for reversing before passing in here -- see
strategy.py where this conversion happens once, in one place.
"""


def ema(values: list[float], period: int) -> list[float | None]:
    """Exponential moving average. Returns a list same length as input;
    first (period - 1) entries are None since EMA needs a seed."""
    if len(values) < period:
        return [None] * len(values)

    result: list[float | None] = [None] * (period - 1)
    multiplier = 2 / (period + 1)

    seed = sum(values[:period]) / period
    result.append(seed)

    prev = seed
    for price in values[period:]:
        current = (price - prev) * multiplier + prev
        result.append(current)
        prev = current

    return result


def true_range(high: float, low: float, prev_close: float) -> float:
    return max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close),
    )


def atr(candles: list[dict], period: int) -> list[float | None]:
    """Average True Range (Wilder's smoothing). candles must be oldest-first."""
    if len(candles) < period + 1:
        return [None] * len(candles)

    trs: list[float] = [None]  # first candle has no prev_close
    for i in range(1, len(candles)):
        tr = true_range(candles[i]["high"], candles[i]["low"], candles[i - 1]["close"])
        trs.append(tr)

    result: list[float | None] = [None] * period
    seed = sum(trs[1:period + 1]) / period
    result.append(seed)

    prev_atr = seed
    for i in range(period + 1, len(trs)):
        current_atr = (prev_atr * (period - 1) + trs[i]) / period
        result.append(current_atr)
        prev_atr = current_atr

    return result


def rolling_high(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for i in range(len(values)):
        if i < window:
            result.append(None)
        else:
            result.append(max(values[i - window:i]))
    return result


def rolling_low(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for i in range(len(values)):
        if i < window:
            result.append(None)
        else:
            result.append(min(values[i - window:i]))
    return result
