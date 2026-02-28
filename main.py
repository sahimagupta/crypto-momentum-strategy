"""
Crypto Momentum Strategy Backtester
------------------------------------
Fetches historical crypto price data and backtests a 
momentum-based moving average crossover strategy.

Usage: python main.py
"""

from data_loader import fetch_crypto_data
from strategy import compute_indicators, generate_signals
from backtester import run_backtest
from utils import calculate_metrics, print_metrics, plot_equity_curve, plot_signals, save_results
from config import (
    SHORT_MA, LONG_MA, MOMENTUM_PERIOD, MOMENTUM_THRESHOLD,
    INITIAL_CAPITAL, TRANSACTION_COST,
    COIN_ID, VS_CURRENCY, LOOKBACK_DAYS, OUTPUT_DIR
)


def main():
    # step 1: get data
    df = fetch_crypto_data(COIN_ID, VS_CURRENCY, LOOKBACK_DAYS)

    # step 2: compute technical indicators
    df = compute_indicators(df, SHORT_MA, LONG_MA, MOMENTUM_PERIOD)

    # step 3: generate trading signals
    df = generate_signals(df, MOMENTUM_THRESHOLD)

    # step 4: run backtest simulation
    results, trades = run_backtest(df, INITIAL_CAPITAL, TRANSACTION_COST)

    # step 5: calculate and display metrics
    metrics = calculate_metrics(results, trades)
    print_metrics(metrics)

    # step 6: save outputs
    plot_equity_curve(results, OUTPUT_DIR)
    plot_signals(df, OUTPUT_DIR)
    save_results(results, trades, OUTPUT_DIR)

    print("Done! Check the 'output' folder for charts and data.")


if __name__ == "__main__":
    main()
