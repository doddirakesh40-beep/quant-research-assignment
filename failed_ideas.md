# Failed Ideas and Experiments

## Task 2 — Shorter Momentum Lookback

### Hypothesis
A shorter momentum lookback of 63 trading days might identify recent stock strength faster than a 126-day lookback.

### Experiment
I changed the `momentum_short` parameter from 126 to 63 while keeping the other strategy parameters unchanged for this comparison.

### Results

| Metric | 63-day test | Earlier 126-day baseline |
|---|---:|---:|
| CAGR | 35.48% | 53.06% |
| Sharpe ratio | 1.290 | 1.638 |
| Maximum drawdown | -23.63% | -22.23% |
| Number of trades | 178 | 119 |

### Conclusion
The 63-day momentum version performed worse than the earlier 126-day baseline on the reported metrics. It had a lower CAGR and Sharpe ratio, a slightly larger maximum drawdown, and more trades.

I therefore did not select the 63-day setting as the preferred version in this comparison.

### Limitation
These results are historical backtest results and do not guarantee future performance. The final preferred parameters must also be evaluated through the assignment's required sensitivity and robustness tests.