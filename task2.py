import numpy as np
import pandas as pd

PARAMS = {
    "n_stocks": 10,
    "momentum_short": 126,
    "momentum_long": 189,
    "trend_window": 200,
    "vol_window": 60,
    "min_turnover": 1e8,
}


def orders(date, hist, portfolio, params, state):
    close = hist["close"]
    volume = hist["volume"]

    # Rebalance on the first trading day of each new month.
    if len(close) < 2:
        return []

    if close.index[-1].month == close.index[-2].month:
        return []

    # Keep enough history for all indicators.
    c = close.iloc[-300:]
    v = volume.reindex(index=c.index, columns=c.columns)

    if len(c) < params["momentum_long"] + 1:
        return []

    # Current prices and momentum.
    price = c.iloc[-1]

    momentum_short = (
        price / c.iloc[-1 - params["momentum_short"]] - 1
    )

    momentum_long = (
        price / c.iloc[-1 - params["momentum_long"]] - 1
    )

    # Long-term trend filter.
    trend = c.rolling(
        params["trend_window"],
        min_periods=params["trend_window"]
    ).mean().iloc[-1]

    above_trend = price > trend

    # Volatility estimate using daily returns.
    daily_returns = c.pct_change(fill_method=None)

    volatility = daily_returns.rolling(
        params["vol_window"],
        min_periods=params["vol_window"]
    ).std().iloc[-1]

    # Liquidity: 60-day median traded value.
    traded_value = c * v

    liquidity = traded_value.rolling(
        60,
        min_periods=40
    ).median().iloc[-1]

    # Require positive momentum, an uptrend and sufficient liquidity.
    eligible = (
        (momentum_short > 0)
        & (momentum_long > 0)
        & above_trend
        & (liquidity >= params["min_turnover"])
        & (volatility > 0)
        & momentum_short.notna()
        & momentum_long.notna()
        & volatility.notna()
        & liquidity.notna()
    )

    # Rank eligible stocks by momentum per unit of volatility.
    score = momentum_short / volatility

    candidates = score[eligible].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    n_stocks = min(int(params["n_stocks"]), 15)

    selected = list(
        candidates.sort_values(ascending=False).index[:n_stocks]
    )

    current_positions = portfolio["positions"]

    # Exit existing holdings that are no longer selected.
    sell_orders = [
        {
            "symbol": symbol,
            "side": "sell",
            "type": "market",
        }
        for symbol in current_positions
        if symbol not in selected
    ]

    # Equal-weight new positions.
    weight = min(1.0 / n_stocks, 0.15)

    buy_orders = [
        {
            "symbol": symbol,
            "side": "buy",
            "type": "market",
            "weight": weight,
            "max_positions": 15,
        }
        for symbol in selected
        if symbol not in current_positions
    ]

    return sell_orders + buy_orders