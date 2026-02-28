import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os


def calculate_metrics(results, trades, risk_free_rate=0.04):
    """
    Calculate key performance metrics for the strategy.
    """
    returns = results["daily_return"].dropna()
    portfolio = results["portfolio_value"]

    # total return
    total_return = (portfolio.iloc[-1] / portfolio.iloc[0]) - 1

    # annualized return (crypto trades 365 days)
    n_days = len(returns)
    annual_return = (1 + total_return) ** (365 / n_days) - 1

    # sharpe ratio (annualized)
    daily_rf = risk_free_rate / 365
    excess_returns = returns - daily_rf
    sharpe = np.sqrt(365) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

    # max drawdown
    rolling_max = portfolio.cummax()
    drawdown = (portfolio - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # win rate from trades
    win_rate = 0
    if len(trades) > 1:
        # pair up buy/sell trades
        buys = trades[trades["action"] == "BUY"].reset_index(drop=True)
        sells = trades[trades["action"] == "SELL"].reset_index(drop=True)
        n_pairs = min(len(buys), len(sells))
        if n_pairs > 0:
            wins = sum(sells.iloc[i]["price"] > buys.iloc[i]["price"] for i in range(n_pairs))
            win_rate = wins / n_pairs

    # buy and hold return for comparison
    bh_return = (results["buy_hold_value"].iloc[-1] / results["buy_hold_value"].iloc[0]) - 1

    # volatility
    annual_vol = returns.std() * np.sqrt(365)

    metrics = {
        "Total Return": f"{total_return:.2%}",
        "Annual Return": f"{annual_return:.2%}",
        "Sharpe Ratio": f"{sharpe:.3f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Win Rate": f"{win_rate:.2%}",
        "Total Trades": len(trades),
        "Annual Volatility": f"{annual_vol:.2%}",
        "Buy & Hold Return": f"{bh_return:.2%}",
        "Final Portfolio": f"",
    }

    return metrics


def print_metrics(metrics):
    """Print performance metrics in a clean format."""
    print("\n" + "=" * 45)
    print("       STRATEGY PERFORMANCE SUMMARY")
    print("=" * 45)
    for key, value in metrics.items():
        print(f"  {key:<22} {value:>15}")
    print("=" * 45 + "\n")


def plot_equity_curve(results, output_dir):
    """Plot portfolio value over time vs buy-and-hold."""
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(results.index, results["portfolio_value"], label="Strategy", linewidth=1.5)
    ax.plot(results.index, results["buy_hold_value"], label="Buy & Hold", linewidth=1.5, alpha=0.7)
    ax.set_title("Portfolio Value: Strategy vs Buy & Hold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = os.path.join(output_dir, "equity_curve.png")
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")


def plot_signals(df, output_dir):
    """Plot price chart with buy/sell markers."""
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1], sharex=True)

    # price + moving averages
    ax1.plot(df.index, df["close"], label="Price", color="black", linewidth=1)
    ax1.plot(df.index, df["sma_short"], label="SMA Short", alpha=0.7)
    ax1.plot(df.index, df["sma_long"], label="SMA Long", alpha=0.7)

    # buy/sell markers
    buys = df[df["trade"] == 1]
    sells = df[df["trade"] == -1]
    ax1.scatter(buys.index, buys["close"], marker="^", color="green", s=100, label="Buy", zorder=5)
    ax1.scatter(sells.index, sells["close"], marker="v", color="red", s=100, label="Sell", zorder=5)

    ax1.set_title("BTC/USD - Momentum Strategy Signals")
    ax1.set_ylabel("Price ($)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # momentum subplot
    ax2.bar(df.index, df["momentum"], color=np.where(df["momentum"] > 0, "green", "red"), alpha=0.6, width=1)
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.set_ylabel("Momentum (%)")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(output_dir, "signals.png")
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")


def save_results(results, trades, output_dir):
    """Save backtest results to CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    results_path = os.path.join(output_dir, "results.csv")
    results.to_csv(results_path)
    print(f"Saved: {results_path}")

    if len(trades) > 0:
        trades_path = os.path.join(output_dir, "trades.csv")
        trades.to_csv(trades_path, index=False)
        print(f"Saved: {trades_path}")

