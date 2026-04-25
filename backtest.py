'''
Simple Backtesting Framework for a Moving Average Crossover Strategy on Binance Data
Strategy:
- Buy when the 20-day Simple Moving Average (SMA) crosses above the 50-day SMA
- Sell when the 20-day SMA crosses below the 50-day SMA
'''

import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SYMBOL       = "BTC/USDT"
TIMEFRAME    = "1d"
LIMIT        = 500 # number of daily candles (~1.5 years)
SHORT_WINDOW = 20
LONG_WINDOW  = 50 

TAKER_FEE = 0.001 # Binance taker rate
SLIPPAGE = 0.0005
COST_PER_TRADE = TAKER_FEE + SLIPPAGE




def fetch_data(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    exchange = ccxt.binance()
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit) # OHLCV: Open, High, Low, Close, and Volume
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"]) # convert raw data (list) into a table
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms") # convert to a readable date format
    df.set_index("timestamp", inplace=True) # set the timestamp as the index
    return df



def compute_signals(df: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    # add moving averages and trade signals to the dataframe
    df["sma_short"] = df["close"].rolling(window=short_window).mean()
    df["sma_long"] = df["close"].rolling(window=long_window).mean()
    df["signal"] = (df["sma_short"] > df["sma_long"]).astype(int) # generate buy signal when short-term MA is above long-term MA
    df["position"] = df["signal"].shift(1) # we can only trade on the next day's open (move the signal down by one day)
    df.dropna(inplace=True) # drop first 50 rows with NaN values (due to rolling mean)
    return df



def compute_metrics(df: pd.DataFrame) -> dict:
    # Raw Returns
    df["market_return"] = df["close"].pct_change()

    # Trade Detection
    df["trade"] = df["position"].diff().abs().fillna(0)
    df.loc[df.index[0], "trade"] = df["position"].iloc[0]
    df["cost"] = df["trade"] * COST_PER_TRADE
 
    # Net Strategy Return
    df["strategy_return_gross"] = df["position"] * df["market_return"]
    df["strategy_return"]       = df["strategy_return_gross"] - df["cost"]

    # Cumulative Wealth Index
    df["cumulative_market_return"] = (1 + df["market_return"]).cumprod()
    df["cumulative_strategy_return_gross"] = (1 + df["strategy_return_gross"]).cumprod()
    df["cumulative_strategy_return"] = (1 + df["strategy_return"]).cumprod()

    #Sharpe Ratio
    daily_mean = df["strategy_return"].mean()
    daily_std = df["strategy_return"].std()
    sharpe = (daily_mean / daily_std) * np.sqrt(365) if daily_std != 0 else 0 # risk-adjusted return (annualised)

    # Maximum Drawdown (worst peak-to-trough decline)
    rolling_peak = df["cumulative_strategy_return"].cummax() # cumulative historial peak
    drawdown = (df["cumulative_strategy_return"] - rolling_peak) / rolling_peak # how far below the peak we are right now
    max_drawdown = drawdown.min() # most negative value = worst loss

    # Total Return
    total_return_strategy = df["cumulative_strategy_return"].iloc[-1] - 1
    total_return_gross    = df["cumulative_strategy_return_gross"].iloc[-1] - 1
    total_return_market = df["cumulative_market_return"].iloc[-1] - 1

    metrics = {
        "Strategy Return (net)": total_return_strategy,
        "Strategy Return (gross)": total_return_gross,
        "Market Return": total_return_market,
        "Sharpe Ratio": round(sharpe, 2),
        "Max Drawdown": max_drawdown,
        "Number of Trades": int(df["trade"].sum())
    }

    return df, metrics



def plot_results(df: pd.DataFrame, metrics: dict) -> None:
    # plot cumulative strategy vs buy-and-hold, with buy/sell markers
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle("BTC/USDT — SMA Crossover Strategy vs. Buy-and-Hold", fontsize=14)

    # cumulative returns plot
    ax1 = axes[0] 
    ax1.plot(df.index, df["cumulative_market_return"], label="Buy-and-Hold", color="blue", linewidth=1.5, linestyle="--")
    ax1.plot(df.index, df["cumulative_strategy_return"], label="SMA Strategy", color="grey", linewidth=1.5)

    buys  = df[(df["trade"] == 1) & (df["position"] == 1)]
    sells = df[(df["trade"] == 1) & (df["position"] == 0)]
    ax1.scatter(buys.index,buys["cumulative_strategy_return"],  marker="^", color="green", zorder=5, s=40, label="Buy")
    ax1.scatter(sells.index,sells["cumulative_strategy_return"], marker="v", color="red",   zorder=5, s=40, label="Sell")

    ax1.set_ylabel("Portfolio Value (starting = 1.0)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    textstr = (f"Strategy Return (net):{metrics['Strategy Return (net)']:.1%}\n"
               f"Strategy Return (gross):{metrics['Strategy Return (gross)']:.1%}\n"
               f"Sharpe Ratio:{metrics['Sharpe Ratio']}\n"
               f"Max Drawdown:{metrics['Max Drawdown']:.2%}\n"
               f"Trades:{metrics['Number of Trades']}\n"
               f"(Fee {TAKER_FEE:.2%} + Slippage {SLIPPAGE:.2%} per trade)"
               )
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, verticalalignment='top', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)) # transform=ax1.transAxes means the coordinates are relative to the axes (0,0 is bottom-left, 1,1 is top-right)

    # price with SMA lines
    ax2 = axes[1]
    ax2.plot(df.index, df["close"], label="BTC Price", color="black", linewidth=0.8)
    ax2.plot(df.index, df["sma_short"], label=f"SMA {SHORT_WINDOW}d", color="blue", linewidth=0.8, alpha=0.8)
    ax2.plot(df.index, df["sma_long"], label=f"SMA {LONG_WINDOW}d", color="red", linewidth=0.8, alpha=0.8)
    ax2.set_ylabel("Price (USDT)")
    ax2.set_xlabel("Date")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y %b')) # date format
    plt.xticks(rotation=45)
    
    plt.tight_layout()

    plt.savefig("backtest_results.png", dpi=500)
    plt.show()



#------Main Execution------

if __name__ == "__main__": # checks if this file is being run directly, or imported into another script
    df = fetch_data(SYMBOL, TIMEFRAME, LIMIT)
    df = compute_signals(df, SHORT_WINDOW, LONG_WINDOW)
    df, metrics = compute_metrics(df)

    print("Backtest Results")
    for key, value in metrics.items():
        if isinstance(value, float):
            # Format as percentage for Return and Drawdown metrics
            if "Return" in key or "Drawdown" in key:
                print(f"{key}: {value:.2%}")
            else:
                print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    plot_results(df, metrics)