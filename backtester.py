"""
Backtesting engine.
Simulates strategy execution on historical data with realistic
transaction costs and position tracking.
"""

import pandas as pd
import numpy as np


def run_backtest(df, initial_capital, transaction_cost, stop_loss=None):
    """
    Run backtest simulation on signal data.

    Simulates a portfolio that goes all-in on buy signals and
    fully exits on sell signals. Applies transaction costs on
    each trade and optionally enforces a stop-loss.

    Args:
        df: DataFrame with 'close', 'position', 'trade' columns
        initial_capital: starting USD amount
        transaction_cost: fraction charged per trade (e.g. 0.001 = 0.1%)
        stop_loss: maximum allowed loss per trade as negative fraction
                   (e.g. -0.05 = -5%). None to disable.

    Returns:
        results: DataFrame with daily portfolio values
        trades: DataFrame with executed trade log
    """
    required = ["close", "position", "trade"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    df = df.copy()

    capital = float(initial_capital)
    holdings = 0.0
    entry_price = 0.0
    portfolio_values = []
    trade_log = []

    for date, row in df.iterrows():
        price = row["close"]
        trade = row["trade"]

        # check stop loss if we have a position
        if stop_loss is not None and holdings > 0 and entry_price > 0:
            current_return = (price - entry_price) / entry_price
            if current_return <= stop_loss:
                # force exit
                revenue = holdings * price
                cost = revenue * transaction_cost
                capital = revenue - cost
                trade_log.append({
                    "date": date,
                    "action": "STOP_LOSS",
                    "price": round(price, 2),
                    "units": round(holdings, 6),
                    "fee": round(cost, 2),
                    "pnl": round(revenue - cost - (holdings * entry_price), 2)
                })
                holdings = 0
                entry_price = 0

        # execute buy
        if trade == 1 and holdings == 0 and capital > 0:
            fee = capital * transaction_cost
            units = (capital - fee) / price
            entry_price = price
            holdings = units
            capital = 0
            trade_log.append({
                "date": date,
                "action": "BUY",
                "price": round(price, 2),
                "units": round(units, 6),
                "fee": round(fee, 2),
                "pnl": 0
            })

        # execute sell
        elif trade == -1 and holdings > 0:
            revenue = holdings * price
            fee = revenue * transaction_cost
            pnl = revenue - fee - (holdings * entry_price)
            capital = revenue - fee
            trade_log.append({
                "date": date,
                "action": "SELL",
                "price": round(price, 2),
                "units": round(holdings, 6),
                "fee": round(fee, 2),
                "pnl": round(pnl, 2)
            })
            holdings = 0
            entry_price = 0

        # track portfolio
        portfolio_value = capital + (holdings * price)
        portfolio_values.append({
            "date": date,
            "portfolio_value": round(portfolio_value, 2),
            "cash": round(capital, 2),
            "holdings": round(holdings, 6),
            "price": round(price, 2),
            "in_position": 1 if holdings > 0 else 0
        })

    # build results dataframe
    results = pd.DataFrame(portfolio_values)
    results.set_index("date", inplace=True)
    results["daily_return"] = results["portfolio_value"].pct_change()
    results["cumulative_return"] = (1 + results["daily_return"]).cumprod() - 1

    # buy-and-hold benchmark
    first_price = df["close"].iloc[0]
    results["buy_hold_value"] = initial_capital * (df["close"] / first_price)

    trades = pd.DataFrame(trade_log)

    total_fees = trades["fee"].sum() if len(trades) > 0 else 0
    total_pnl = trades["pnl"].sum() if len(trades) > 0 else 0

    print("[+] Backtest done: {} trades, fees=${:.2f}, net P&L=${:.2f}".format(len(trade_log), total_fees, total_pnl))

    return results, trades
