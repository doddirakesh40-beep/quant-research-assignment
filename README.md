# H TO H PARTNERS LLP: Quant Research Intern take-home, data pack

This pack has the data, the two strategy templates and the backtest harness for both tasks.
The task descriptions are in the assignment email. This file covers the data, the interfaces and the rules.

```
data/
  nifty50_15min_train_2017-04-03_2022-01-31.csv       Task 1 bars
  nifty_monthly_expiries_2017-01_2022-01.csv          Task 1 monthly futures expiries (for roll cost)
  stocks_daily_train_2021-04-26_2024-06-30.csv        Task 2 daily OHLCV, 555 NSE stocks
  nifty50_daily_2021-04-26_2024-06-30.csv             Task 2 Nifty 50 index daily OHLC
  symbols.txt                                         Task 2 stock list
task1_template.py      Task 1 interface + trivial example (moving-average crossover)
task2_template.py      Task 2 interface + trivial example (top-10 by 6-month return, monthly)
harness_public.py      the backtest accounting for both tasks
```

Requirements: Python 3.9+, numpy, pandas. Nothing else is needed.

```
python harness_public.py task1 task1.py
python harness_public.py task2 task2.py
```

We score your submission with an identical copy of `harness_public.py` on data you do not have, so do not change
the harness and do not rely on anything it does not give you.

## Task 1: Nifty 50 futures on 15-minute bars

### Data
`nifty50_15min_train_2017-04-03_2022-01-31.csv`: Nifty 50 **spot index** 15-minute bars, 29,803 rows.

| column | meaning |
|---|---|
| datetime | bar **start** time, IST, `YYYY-MM-DD HH:MM:SS`. Bars are 09:15, 09:30, ... 15:15 (25 per normal day) |
| open, high, low, close | index levels |
| n_1min | number of 1-minute candles that formed the bar (normally 15) |

There is no volume (it is an index). Bars were resampled from public 1-minute data.
A few bars have fewer than 15 one-minute candles. Short Muhurat trading sessions exist on 2021-11-04 (3 bars) in this
file, and on 2024-03-02, 2024-05-18 and 2025-10-21 later on; your code must handle days with fewer than 25 bars.

`nifty_monthly_expiries_2017-01_2022-01.csv`: one date per month. The rule used is last Thursday of the month
(last Tuesday from Sep-2025), moved to the previous trading day on holidays, computed from the trading calendar.
This is an approximation; it can differ from the exact NSE calendar on a few holiday months. That is fine: it only
decides on which night the roll cost is charged.

### Interface
```python
PARAMS = {...}                                # at most 6 entries
def positions(bars: pd.DataFrame, params: dict) -> pd.Series:
    ...                                       # one value per bar, in {-1, 0, +1}
```
* The value at bar *i* is the position you want, decided at the **close of bar i** using bars 0..i only.
* The harness fills it at the **open of bar i+1**. Positions are 1x capital (no leverage) and carried overnight.
* The harness checks for look-ahead by re-running `positions()` on truncated data and comparing the last value.
* **Warm-up:** the first 200 bars are always flat. Your function receives all bars from the first one, so use them for
  indicator warm-up.

### Accounting (all as a fraction of capital)
* The position is a Nifty futures position. We model futures P&L as spot P&L plus carry.
* Overnight gap `pos * (open / previous close - 1)` accrues to the position held from the previous close.
* Cost **0.025% of notional per side** on every position change (`|new - old| * 0.025%`, so a flip from +1 to -1 pays 2 sides).
* **Roll:** a position held through a monthly expiry pays 2 sides (0.05%) on the next day.
* **Carry:** a position held overnight pays `pos * (6% - 1.3%) / 252` per night (futures premium; 1.3% is the dividend yield).
  A short position receives it.
* **Cash:** capital earns 6% a year (`6%/252` per trading day) whether you are in the market or not (margin sits in a liquid fund).
* Returns are summed within a day and compounded daily.

## Task 2: long-only NSE stock portfolio on daily bars

### Data
`stocks_daily_train_2021-04-26_2024-06-30.csv`: columns `date, symbol, open, high, low, close, volume`, one row per
stock per trading day. Source: Zerodha Kite historical daily candles, NSE cash market. Prices in INR, volume in shares.
Prices are adjusted for splits and bonuses, **not** for dividends. A stock has no rows before it listed.

`nifty50_daily_2021-04-26_2024-06-30.csv`: Nifty 50 index daily OHLC (volume = 0). Use it for regime filters if you like.
`symbols.txt`: the 555 symbols in the file.

**Survivorship bias.** The stock list is the set of NSE stocks that were liquid (60-day median traded value >= Rs 10 crore)
in **October 2026**. Stocks that were liquid in 2022 but have since been delisted, merged or become illiquid are missing.
This flatters every long-only strategy, especially momentum and small-cap tilts. Say in your report how you think it
affects your results. A liquidity filter applied on each day (as in the template) is still a good idea.

**Corporate-action anomalies.** We did not re-verify every corporate action. Across our full data set five stocks have a
one-day close drop of more than 45% that looks like a demerger or an unadjusted event: **ABFRL, STAR, INDIAGLYCO,
SPLPETRO, ALLCARGO**. Only SPLPETRO (2022-06-07) falls inside your file; the others happen in the period we test on.
Your code should not break or blow up on such a jump. Handle them as you see fit and say what you did.

### Warm-up and evaluation window
Data starts 2021-04-26 so you have about 10 months of warm-up. The harness trades and scores only the
**evaluation window 2 Mar 2022 to 30 Jun 2024**. `orders()` is first called on the close of the last day before the window.
Long lookbacks (e.g. 252 days) are not fully available at the start of the window; handle that in your code.

### Interface
```python
PARAMS = {...}                                # at most 6 entries
def orders(date, hist, portfolio, params, state) -> list:
    ...
```
Called once per trading day **after the close**. `hist` contains data up to and including `date` only:
`hist['open'|'high'|'low'|'close'|'volume']` are DataFrames (index = date, columns = symbol, NaN before listing) and
`hist['nifty']` is the index OHLC. `portfolio` gives cash, total value and your open positions. `state` is a dict that
persists between calls.

The orders you return are executed on the **next trading day only**; anything not filled is cancelled.

| order | fills |
|---|---|
| `{'symbol': s, 'side': 'buy', 'type': 'market', 'weight': w}` | at the next open |
| `{'symbol': s, 'side': 'buy', 'type': 'stop', 'trigger': x, 'weight': w}` | if next day's high > x, at max(open, x) |
| `{'symbol': s, 'side': 'sell', 'type': 'market'}` | whole position at the next open |
| `{'symbol': s, 'side': 'sell', 'type': 'stop', 'trigger': x}` | if next day's low < x, at min(open, x) |

* `weight` = fraction of the portfolio value at the decision close. Maximum **15%** per new position, maximum
  **15 open positions**, no leverage (a buy is cut to the cash available), no shorting, no adding to an open position.
* Optional `'max_positions': k` on a buy: it fills only while fewer than k positions are open. With many stop orders
  this lets you say "take the first k that trigger, in the order I listed them".
* Order of execution on the next day: market sells at the open, then buys in the order you listed them, then stop sells.
  A stop sell does not apply to a position bought the same day. Cash from a stop sell is available the following day.
* Orders on a symbol with no price that day lapse.
* Cost **0.2% per side** (brokerage, STT, slippage): shares bought = amount x (1 - 0.2%) / price; sale proceeds =
  shares x price x (1 - 0.2%). Idle cash earns nothing in Task 2.
* Positions are valued at the latest available close.

## What the harness reports
CAGR, total return, max drawdown, Sharpe (daily returns, annualised with sqrt(252), in excess of what idle cash earns:
6% for Task 1, 0% for Task 2), Calmar, number of trades, win rate, average trade, turnover, time in market and a year-wise
return table.

## Rules
* Deterministic: the same input gives the same output. If you use randomness, fix the seed.
* No hard-coded dates or date ranges in the strategy logic (e.g. "skip 2020"). The calendar can only enter through the data.
* No external data and no reading the data files from inside `positions()` / `orders()`.
* At most **6 tunable parameters** per task, all in `PARAMS`. Fixed constants that you did not tune (e.g. 252 days per year)
  do not count; anything you tried more than one value of does.
* The harness must run your file unchanged in a few minutes on a laptop.

## Submission
One zip named `<your_name>.zip` containing:
```
task1.py          your Task 1 strategy (from task1_template.py)
task2.py          your Task 2 strategy (from task2_template.py)
report.pdf        your write-up (see the email for what it should cover)
failed_ideas.md   what you tried that did not work, and why you think it failed
```
plus any helper .py files your code imports. Do not include the data folder or the harness.
