"""
Task 1: Nifty 50 15-minute long-only trend/breakout strategy.

Signal:
- Enter long when close breaks above the highest high of the previous breakout_lookback bars
  and close is above the long-term EMA.
- Exit when close falls below the lowest low of the previous exit_lookback bars or below
  the long-term EMA.
- All channel levels exclude the current bar. The harness fills signals at the next bar's open.

This is a candidate research strategy, not a guarantee of out-of-sample performance.
"""
import numpy as np
import pandas as pd

PARAMS = {
    "breakout_lookback": 15,
    "trend_ema": 150,
    "exit_lookback": 20,
}


def positions(bars: pd.DataFrame, params: dict) -> pd.Series:
    close = bars["close"]
    high = bars["high"]
    low = bars["low"]

    trend = close.ewm(
        span=int(params["trend_ema"]), adjust=False,
        min_periods=int(params["trend_ema"])
    ).mean()

    # Shift by one bar so the current bar cannot set its own breakout/exit threshold.
    prior_high = high.shift(1).rolling(
        int(params["breakout_lookback"]),
        min_periods=int(params["breakout_lookback"])
    ).max()
    prior_exit_low = low.shift(1).rolling(
        int(params["exit_lookback"]),
        min_periods=int(params["exit_lookback"])
    ).min()

    out = np.zeros(len(bars), dtype=float)
    in_position = False

    for i in range(len(bars)):
        # The assignment specifies that the first 200 bars are warm-up only.
        if i < 200:
            out[i] = 0.0
            continue

        values = (trend.iloc[i], prior_high.iloc[i], prior_exit_low.iloc[i])
        if any(pd.isna(v) for v in values):
            out[i] = 0.0
            continue

        c = close.iloc[i]

        if in_position and (c < prior_exit_low.iloc[i] or c < trend.iloc[i]):
            in_position = False

        if not in_position and c > prior_high.iloc[i] and c > trend.iloc[i]:
            in_position = True

        out[i] = 1.0 if in_position else 0.0

    return pd.Series(out, index=bars.index, dtype=float)
