"""
Quick sanity checks for indicators.py and strategy.py using synthetic data.
Not a full test suite -- just enough to catch obvious bugs before deploying.
Run with: python -m bot.test_sanity
"""

import random

from bot import indicators
from bot.premarket import compute_pivot_levels, pivot_levels_from_daily_candles
from bot.strategy import evaluate


def make_synthetic_candles(n=60, start_price=6900, trend=0.5, volatility=8):
    """Generates fake oldest-first OHLC candles for testing, then returns
    them in Upstox's newest-first raw array format (to mimic the real API)."""
    candles = []
    price = start_price
    for i in range(n):
        price += trend + random.uniform(-volatility, volatility)
        high = price + random.uniform(0, volatility)
        low = price - random.uniform(0, volatility)
        open_ = price - random.uniform(-volatility / 2, volatility / 2)
        close = price
        candles.append([f"2026-06-24T{9 + i // 12:02d}:{(i % 12) * 5:02d}:00+05:30",
                         open_, high, low, close, 1000])
    candles.reverse()  # newest-first, like Upstox returns
    return candles


def test_ema_basic():
    values = [float(x) for x in range(1, 31)]
    result = indicators.ema(values, 9)
    assert result[8] is not None, "EMA should have a value once seed period reached"
    assert all(v is None for v in result[:8]), "EMA should be None before seed period"
    print("✓ EMA basic test passed")


def test_atr_basic():
    candles = make_synthetic_candles(40)
    parsed = []
    for c in reversed(candles):
        parsed.append({"timestamp": c[0], "open": c[1], "high": c[2], "low": c[3], "close": c[4]})
    result = indicators.atr(parsed, 14)
    assert result[14] is not None, "ATR should have a value once seed period reached"
    assert result[14] > 0, "ATR should be positive"
    print(f"✓ ATR basic test passed (sample value: {result[20]:.2f})")


def test_strategy_runs_without_crashing():
    candles = make_synthetic_candles(60, trend=2.0)  # strong uptrend
    signal = evaluate(candles)
    print(f"✓ Strategy evaluated without error. Signal: {signal}")


def test_strategy_insufficient_data():
    candles = make_synthetic_candles(5)  # too few candles
    signal = evaluate(candles)
    assert signal is None, "Should return None when insufficient data"
    print("✓ Insufficient-data guard works")


def test_pivot_levels():
    levels = compute_pivot_levels(prev_high=7050.0, prev_low=6920.0, prev_close=7030.0)
    # Sanity: pivot should sit between low and high
    assert levels.prev_low <= levels.pivot <= levels.prev_high
    # R1 > pivot > S1, by construction of the classic formula
    assert levels.r1 > levels.pivot > levels.s1
    assert levels.r2 > levels.r1
    assert levels.r3 > levels.r2
    assert levels.s2 < levels.s1
    assert levels.s3 < levels.s2

    raw_daily = [
        ['2026-06-23T00:00:00+05:30', 6960.0, 7050.0, 6920.0, 7030.0, 50000, 0],
    ]
    levels_from_raw = pivot_levels_from_daily_candles(raw_daily)
    assert levels_from_raw.pivot == levels.pivot
    print(f"✓ Pivot levels test passed (pivot={levels.pivot}, R1={levels.r1}, S1={levels.s1})")


if __name__ == "__main__":
    test_ema_basic()
    test_atr_basic()
    test_strategy_runs_without_crashing()
    test_strategy_insufficient_data()
    test_pivot_levels()
    print("\nAll sanity checks passed.")
