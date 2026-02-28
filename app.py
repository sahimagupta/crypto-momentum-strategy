"""
Web dashboard for the crypto momentum backtester.
Run: python app.py
Open: http://localhost:5000
"""

import os
import io
import base64
import json
from flask import Flask, render_template, request, jsonify

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from data_loader import fetch_crypto_data, DataLoadError
from strategy import compute_indicators, generate_signals
from backtester import run_backtest
from utils import calculate_metrics

app = Flask(__name__, template_folder="templates", static_folder="static")


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string for embedding in HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="#1a1a2e")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def make_equity_chart(results):
    """Generate equity curve chart."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6),
                                    height_ratios=[3, 1], sharex=True,
                                    facecolor="#1a1a2e")

    for ax in [ax1, ax2]:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("#333")
        ax.spines["top"].set_color("#333")
        ax.spines["left"].set_color("#333")
        ax.spines["right"].set_color("#333")

    ax1.plot(results.index, results["portfolio_value"],
             label="Strategy", linewidth=2, color="#00d2ff")
    ax1.plot(results.index, results["buy_hold_value"],
             label="Buy & Hold", linewidth=2, color="#ff6b6b", alpha=0.8)
    ax1.fill_between(results.index, results["portfolio_value"],
                      results["buy_hold_value"], alpha=0.15,
                      where=results["portfolio_value"] >= results["buy_hold_value"],
                      color="#00ff88")
    ax1.fill_between(results.index, results["portfolio_value"],
                      results["buy_hold_value"], alpha=0.15,
                      where=results["portfolio_value"] < results["buy_hold_value"],
                      color="#ff4444")

    ax1.set_title("Portfolio Value: Strategy vs Buy & Hold",
                   fontsize=13, fontweight="bold", color="white")
    ax1.set_ylabel("Value ($)", color="white")
    ax1.legend(loc="upper left", fontsize=9, facecolor="#16213e",
               edgecolor="#333", labelcolor="white")
    ax1.grid(True, alpha=0.15, color="gray")

    rolling_max = results["portfolio_value"].cummax()
    drawdown = (results["portfolio_value"] - rolling_max) / rolling_max * 100
    ax2.fill_between(results.index, drawdown, 0, alpha=0.5, color="#ff4444")
    ax2.set_ylabel("Drawdown %", color="white")
    ax2.grid(True, alpha=0.15, color="gray")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    plt.tight_layout()
    return fig_to_base64(fig)


def make_signals_chart(df, short_ma, long_ma):
    """Generate trading signals chart."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6),
                                    height_ratios=[3, 1], sharex=True,
                                    facecolor="#1a1a2e")

    for ax in [ax1, ax2]:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("#333")
        ax.spines["top"].set_color("#333")
        ax.spines["left"].set_color("#333")
        ax.spines["right"].set_color("#333")

    ax1.plot(df.index, df["close"], label="Price", color="white", linewidth=1.2)
    ax1.plot(df.index, df["sma_short"], label="SMA {}".format(short_ma),
             color="#00d2ff", alpha=0.8)
    ax1.plot(df.index, df["sma_long"], label="SMA {}".format(long_ma),
             color="#ff9800", alpha=0.8)

    if "bb_upper" in df.columns:
        ax1.fill_between(df.index, df["bb_lower"], df["bb_upper"],
                          alpha=0.05, color="white")

    buys = df[df["trade"] == 1]
    sells = df[df["trade"] == -1]
    ax1.scatter(buys.index, buys["close"], marker="^", color="#00ff88",
                s=120, label="Buy", zorder=5, edgecolors="white", linewidth=0.5)
    ax1.scatter(sells.index, sells["close"], marker="v", color="#ff4444",
                s=120, label="Sell", zorder=5, edgecolors="white", linewidth=0.5)

    ax1.set_title("Price Action with Trading Signals",
                   fontsize=13, fontweight="bold", color="white")
    ax1.set_ylabel("Price ($)", color="white")
    ax1.legend(loc="upper left", fontsize=8, facecolor="#16213e",
               edgecolor="#333", labelcolor="white")
    ax1.grid(True, alpha=0.15, color="gray")

    colors = np.where(df["momentum"] > 0, "#00ff88", "#ff4444")
    ax2.bar(df.index, df["momentum"], color=colors, alpha=0.6, width=1)
    ax2.axhline(y=0, color="gray", linewidth=0.5)
    ax2.set_ylabel("Momentum %", color="white")
    ax2.grid(True, alpha=0.15, color="gray")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    plt.tight_layout()
    return fig_to_base64(fig)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_strategy():
    try:
        data = request.json
        coin = data.get("coin", "bitcoin")
        days = int(data.get("days", 365))
        short_ma = int(data.get("short_ma", 20))
        long_ma = int(data.get("long_ma", 50))
        capital = float(data.get("capital", 10000))
        stop_loss = float(data.get("stop_loss", -0.05))

        if short_ma >= long_ma:
            return jsonify({"error": "Short MA must be less than Long MA"}), 400

        # run the strategy
        df = fetch_crypto_data(coin, "usd", days)
        df = compute_indicators(df, short_ma, long_ma, 14)
        df = generate_signals(df, 0)
        results, trades = run_backtest(df, capital, 0.001, stop_loss)
        metrics = calculate_metrics(results, trades)

        # generate charts
        equity_chart = make_equity_chart(results)
        signals_chart = make_signals_chart(df, short_ma, long_ma)

        # trade log for table
        trade_list = []
        if len(trades) > 0:
            for _, t in trades.iterrows():
                trade_list.append({
                    "date": str(t["date"])[:10] if "date" in t else "",
                    "action": t.get("action", ""),
                    "price": t.get("price", 0),
                    "units": round(t.get("units", 0), 6),
                    "fee": t.get("fee", 0),
                    "pnl": t.get("pnl", 0),
                })

        return jsonify({
            "metrics": metrics,
            "equity_chart": equity_chart,
            "signals_chart": signals_chart,
            "trades": trade_list,
            "data_points": len(df),
        })

    except DataLoadError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    print("\n  Crypto Momentum Backtester")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(debug=False, port=5000)
