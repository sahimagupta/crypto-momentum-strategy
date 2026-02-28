"""
Crypto Momentum Strategy Backtester
====================================
Backtests a momentum-based moving average crossover strategy
on cryptocurrency market data.

Usage:
    python main.py                          # default: BTC, 1 year
    python main.py --coin ethereum          # test on ETH
    python main.py --days 730               # 2 years of data
    python main.py --short-ma 10 --long-ma 30   # custom MA periods
    python main.py --compare                # compare across multiple coins
"""

import argparse
import sys
import os

from data_loader import fetch_crypto_data, DataLoadError
from strategy import compute_indicators, generate_signals
from backtester import run_backtest
from utils import (
    calculate_metrics, print_metrics,
    plot_equity_curve, plot_signals, save_results
)
from config import (
    SHORT_MA, LONG_MA, MOMENTUM_PERIOD, MOMENTUM_THRESHOLD,
    INITIAL_CAPITAL, TRANSACTION_COST, STOP_LOSS,
    COIN_ID, VS_CURRENCY, LOOKBACK_DAYS, OUTPUT_DIR,
    SUPPORTED_COINS
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backtest momentum strategy on crypto data"
    )
    parser.add_argument("--coin", default=COIN_ID,
                        help=f"coin to test (default: {COIN_ID})")
    parser.add_argument("--days", type=int, default=LOOKBACK_DAYS,
                        help=f"lookback period in days (default: {LOOKBACK_DAYS})")
    parser.add_argument("--short-ma", type=int, default=SHORT_MA,
                        help=f"short MA window (default: {SHORT_MA})")
    parser.add_argument("--long-ma", type=int, default=LONG_MA,
                        help=f"long MA window (default: {LONG_MA})")
    parser.add_argument("--capital", type=float, default=INITIAL_CAPITAL,
                        help=f"starting capital (default: {INITIAL_CAPITAL})")
    parser.add_argument("--no-stop-loss", action="store_true",
                        help="disable stop-loss")
    parser.add_argument("--compare", action="store_true",
                        help="compare strategy across multiple coins")
    return parser.parse_args()


def run_single(coin, days, short_ma, long_ma, capital, stop_loss, output_dir):
    """Run backtest for a single coin."""
    print(f"\n{'='*50}")
    print(f"  BACKTESTING: {coin.upper()}")
    print(f"  Period: {days} days | MA: {short_ma}/{long_ma}")
    print("  Capital: ${:,.0f} | Stop-loss: {}".format(capital, stop_loss))
    print(f"{'='*50}\n")

    # fetch data
    df = fetch_crypto_data(coin, VS_CURRENCY, days)

    # compute indicators
    df = compute_indicators(df, short_ma, long_ma, MOMENTUM_PERIOD)

    # generate signals
    df = generate_signals(df, MOMENTUM_THRESHOLD)

    # run simulation
    results, trades = run_backtest(df, capital, TRANSACTION_COST, stop_loss)

    # calculate and show metrics
    metrics = calculate_metrics(results, trades)
    print_metrics(metrics)

    # save outputs
    coin_dir = os.path.join(output_dir, coin)
    plot_equity_curve(results, coin_dir)
    plot_signals(df, coin_dir, short_ma, long_ma)
    save_results(results, trades, coin_dir)

    return metrics


def run_comparison(coins, days, short_ma, long_ma, capital, stop_loss, output_dir):
    """Run backtest across multiple coins and compare."""
    all_metrics = {}

    for coin in coins:
        try:
            metrics = run_single(coin, days, short_ma, long_ma,
                                capital, stop_loss, output_dir)
            all_metrics[coin] = metrics
        except DataLoadError as e:
            print(f"[!] Skipping {coin}: {e}")
        except Exception as e:
            print(f"[!] Error with {coin}: {e}")

    # print comparison table
    if len(all_metrics) > 1:
        print(f"\n{'='*70}")
        print("  COMPARISON ACROSS COINS")
        print(f"{'='*70}")
        header = f"  {'Coin':<12} {'Return':>10} {'Sharpe':>10} {'MaxDD':>10} {'WinRate':>10}"
        print(header)
        print(f"  {'-'*52}")
        for coin, m in all_metrics.items():
            print(f"  {coin.upper():<12} {m['Total Return']:>10} {m['Sharpe Ratio']:>10} "
                  f"{m['Max Drawdown']:>10} {m['Win Rate']:>10}")
        print(f"{'='*70}")


def main():
    args = parse_args()

    stop_loss = None if args.no_stop_loss else STOP_LOSS

    try:
        if args.compare:
            run_comparison(SUPPORTED_COINS, args.days, args.short_ma,
                          args.long_ma, args.capital, stop_loss, OUTPUT_DIR)
        else:
            run_single(args.coin, args.days, args.short_ma, args.long_ma,
                      args.capital, stop_loss, OUTPUT_DIR)

        print("\nDone. Results saved in 'output/' folder.")

    except DataLoadError as e:
        print(f"\n[ERROR] Data loading failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
