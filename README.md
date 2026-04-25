# BTC/USDT SMA Crossover Backtest

A quantitative backtest of a Simple Moving Average (SMA) crossover strategy on Bitcoin daily price data, built from scratch in Python using live Binance API data.

> Results are generated from a rolling 500-day live Binance feed and results will vary by run date.

## Strategy
- **Signal**: Buy when the 20-day SMA crosses above the 50-day SMA; sell to cash when it crosses below.
- **Data**: Daily OHLCV from Binance via `ccxt` (~500 days)
- **Lookahead bias**: Avoided by shifting signals by 1 period.

## Performance Metrics
| Metric | Value |
|---|---|
| Strategy Return (net) | −5.62% |
| Strategy Return (gross) | −3.75% |
| Market Return (BTC) | −25.95% |
| Sharpe Ratio | −0.05 |
| Max Drawdown | −28.98% |
| Number of Trades | 13 |

## Cost Model
| Cost Component | Rate |
|---|---|
| Taker fee | 0.10% |
| Slippage | 0.05% |
| Total per trade | 0.15% |

 
## Output
![BTC/USDT SMA Crossover Backtest Results](backtest_results.png)

## Key Findings

**Structural Strategy Constraints**: The negative Sharpe (−0.05) indicates risk-adjusted returns remain below the risk-free rate despite outperforming buy-and-hold in absolute terms. This is expected — a dual SMA crossover is a lagging, single-signal strategy with no volatility filtering, position sizing, or regime awareness. Whipsaw losses in sideways markets are structurally inevitable. A more sophisticated strategy is in development.

**Downside protection**: The strategy lost −5.62% over the study period against a BTC buy-and-hold return of −25.95%, representing **+20.33 percentage points of outperformance** in a declining market.
 
**Transaction cost impact**: Gross return was −3.75% vs net −5.62%, meaning 13 trades across ~500 days produced −1.87% of total cost drag (0.15% per trade).


## Setup

```bash
pip install ccxt pandas numpy matplotlib
python backtest.py
```