"""
Utility functions for metrics calculation, plotting, and export.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for saving plots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os


def calculate_metrics(results, trades, risk_free_rate=0.04):
    """
    Compute performance metrics for the strategy.

    Args:
        results: DataFrame from run_backtest()
        trades: DataFrame of trade log
        risk_free_rate: annual risk-free rate (default 4%)

    Returns:
        dict of metric name -> value
    """
    returns = results["daily_return"].dropna()
    portfolio = results["portfolio_value"]

    # basic returns
    total_return = (portfolio.iloc[-1] / portfolio.iloc[0]) - 1
    n_days = len(returns)
    annual_return = (1 + total_return) ** (365 / max(n_days, 1)) - 1

    # risk metrics
    daily_rf = risk_free_rate / 365
    excess = returns - daily_rf
    sharpe = (np.sqrt(365) * excess.mean() / excess.std()) if excess.std() > 0 else 0.0

    # sortino ratio (downside deviation only)
    downside = excess[excess < 0]
    downside_std = downside.std() if len(downside) > 0 else 1e-9
    sortino = (np.sqrt(365) * excess.mean() / downside_std) if downside_std > 0 else 0.0

    # drawdown analysis
    rolling_max = portfolio.cummax()
    drawdown = (portfolio - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # find max drawdown duration
    in_dd = drawdown < 0
    dd_groups = (~in_dd).cumsum()
    if in_dd.any():
        dd_lengths = in_dd.groupby(dd_groups).sum()
        max_dd_duration = dd_lengths.max()
    else:
        max_dd_duration = 0

    # trade analysis
    win_rate = 0.0
    avg_win = 0.0
    avg_loss = 0.0
    profit_factor = 0.0

    if len(trades) > 0 and "pnl" in trades.columns:
        closed = trades[trades["action"].isin(["SELL", "STOP_LOSS"])]
        if len(closed) > 0:
            wins = closed[closed["pnl"] > 0]
            losses = closed[closed["pnl"] <= 0]
            win_rate = len(wins) / len(closed)
            avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
            avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
            total_wins = wins["pnl"].sum() if len(wins) > 0 else 0
            total_losses = abs(losses["pnl"].sum()) if len(losses) > 0 else 1e-9
            profit_factor = total_wins / total_losses

    # buy and hold benchmark
    bh_return = (results["buy_hold_value"].iloc[-1] / results["buy_hold_value"].iloc[0]) - 1

    # volatility
    annual_vol = returns.std() * np.sqrt(365)

    # calmar ratio
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    metrics = {
        "Total Return": f"{total_return:.2%}",
        "Annual Return": f"{annual_return:.2%}",
        "Sharpe Ratio": f"{sharpe:.3f}",
        "Sortino Ratio": f"{sortino:.3f}",
        "Calmar Ratio": f"{calmar:.3f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Max DD Duration": f"{int(max_dd_duration)} days",
        "Annual Volatility": f"{annual_vol:.2%}",
        "Win Rate": f"{win_rate:.1%}",
        "Avg Win": "${:.2f}".format(avg_win),
        "Avg Loss": "${:.2f}".format(avg_loss),
        "Profit Factor": f"{profit_factor:.2f}",
        "Total Trades": len(trades),
        "Buy & Hold Return": f"{bh_return:.2%}",
        "Final Portfolio": "${:,.2f}".format(portfolio.iloc[-1]),
    }

    return metrics


def print_metrics(metrics):
    """Display metrics in a formatted table."""
    print("\n" + "=" * 50)
    print("         STRATEGY PERFORMANCE SUMMARY")
    print("=" * 50)
    for key, value in metrics.items():
        print(f"  {key:<22} {str(value):>20}")
    print("=" * 50)


def plot_equity_curve(results, output_dir):
    """
    Plot portfolio equity curve vs buy-and-hold benchmark.
    Also shows drawdown in a subplot.
    """
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                    height_ratios=[3, 1], sharex=True)

    # equity curves
    ax1.plot(results.index, results["portfolio_value"],
             label="Strategy", linewidth=1.5, color="#2196F3")
    ax1.plot(results.index, results["buy_hold_value"],
             label="Buy & Hold", linewidth=1.5, color="#FF9800", alpha=0.8)
    ax1.fill_between(results.index, results["portfolio_value"],
                      results["buy_hold_value"], alpha=0.1,
                      where=results["portfolio_value"] >= results["buy_hold_value"],
                      color="green", label="Outperformance")
    ax1.fill_between(results.index, results["portfolio_value"],
                      results["buy_hold_value"], alpha=0.1,
                      where=results["portfolio_value"] < results["buy_hold_value"],
                      color="red", label="Underperformance")

    ax1.set_title("Portfolio Value: Strategy vs Buy & Hold", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Portfolio Value ($)")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.3)

    # drawdown subplot
    rolling_max = results["portfolio_value"].cummax()
    drawdown = (results["portfolio_value"] - rolling_max) / rolling_max * 100
    ax2.fill_between(results.index, drawdown, 0, alpha=0.4, color="red")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()

    path = os.path.join(output_dir, "equity_curve.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {path}")


def plot_signals(df, output_dir, short_window=20, long_window=50):
    """
    Plot price with MA lines, buy/sell markers, and momentum indicator.
    """
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(14, 10),
                              height_ratios=[3, 1, 1], sharex=True)

    ax1, ax2, ax3 = axes

    # price and moving averages
    ax1.plot(df.index, df["close"], label="Price", color="black", linewidth=1)
    ax1.plot(df.index, df["sma_short"], label=f"SMA {short_window}",
             color="#2196F3", alpha=0.7)
    ax1.plot(df.index, df["sma_long"], label=f"SMA {long_window}",
             color="#FF9800", alpha=0.7)

    # bollinger bands
    if "bb_upper" in df.columns:
        ax1.fill_between(df.index, df["bb_lower"], df["bb_upper"],
                          alpha=0.05, color="gray", label="Bollinger Bands")

    # trade markers
    buys = df[df["trade"] == 1]
    sells = df[df["trade"] == -1]
    ax1.scatter(buys.index, buys["close"], marker="^", color="#4CAF50",
                s=120, label="Buy", zorder=5, edgecolors="black", linewidth=0.5)
    ax1.scatter(sells.index, sells["close"], marker="v", color="#F44336",
                s=120, label="Sell", zorder=5, edgecolors="black", linewidth=0.5)

    ax1.set_title("Price Action with Trading Signals", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Price ($)")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # momentum
    colors = np.where(df["momentum"] > 0, "#4CAF50", "#F44336")
    ax2.bar(df.index, df["momentum"], color=colors, alpha=0.6, width=1)
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.set_ylabel("Momentum (%)")
    ax2.grid(True, alpha=0.3)

    # volume
    if "volume" in df.columns:
        vol_colors = np.where(df["close"].diff() >= 0, "#4CAF50", "#F44336")
        ax3.bar(df.index, df["volume"], color=vol_colors, alpha=0.5, width=1)
        if "vol_ma" in df.columns:
            ax3.plot(df.index, df["vol_ma"], color="orange", linewidth=1, label="Vol MA")
            ax3.legend(fontsize=8)
        ax3.set_ylabel("Volume")
    else:
        ax3.text(0.5, 0.5, "Volume data not available", transform=ax3.transAxes,
                 ha="center", va="center", fontsize=12, color="gray")

    ax3.set_xlabel("Date")
    ax3.grid(True, alpha=0.3)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.tight_layout()

    path = os.path.join(output_dir, "signals.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {path}")


def save_results(results, trades, output_dir):
    """Export backtest results and trade log to CSV."""
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, "daily_portfolio.csv")
    results.to_csv(path)
    print(f"[+] Saved: {path}")

    if len(trades) > 0:
        path = os.path.join(output_dir, "trade_log.csv")
        trades.to_csv(path, index=False)
        print(f"[+] Saved: {path}")

