import pandas as pd
import numpy as np


def run_backtest(df, initial_capital, transaction_cost):
    """
    Simulate trading strategy on historical data.
    
    Tracks portfolio value, cash, holdings, and trade log.
    Applies transaction costs on each trade.
    
    Returns:
        DataFrame with portfolio values and trade details
    """
    df = df.copy()

    capital = initial_capital
    holdings = 0.0       # number of units held
    portfolio_values = []
    trade_log = []

    for i, (date, row) in enumerate(df.iterrows()):
        price = row["close"]
        position = row["position"]
        trade = row["trade"]

        # execute trade if signal changed
        if trade == 1:  # buy signal
            # invest all capital
            cost = capital * transaction_cost
            units = (capital - cost) / price
            holdings = units
            capital = 0
            trade_log.append({
                "date": date,
                "action": "BUY",
                "price": price,
                "units": units,
                "cost": cost
            })

        elif trade == -1 and holdings > 0:  # sell signal
            revenue = holdings * price
            cost = revenue * transaction_cost
            capital = revenue - cost
            trade_log.append({
                "date": date,
                "action": "SELL",
                "price": price,
                "units": holdings,
                "cost": cost
            })
            holdings = 0

        # calculate current portfolio value
        portfolio_value = capital + (holdings * price)
        portfolio_values.append({
            "date": date,
            "portfolio_value": portfolio_value,
            "capital": capital,
            "holdings": holdings,
            "price": price
        })

    # build results
    results = pd.DataFrame(portfolio_values)
    results.set_index("date", inplace=True)
    results["daily_return"] = results["portfolio_value"].pct_change()

    # buy and hold comparison
    results["buy_hold_value"] = initial_capital * (df["close"] / df["close"].iloc[0])

    trades = pd.DataFrame(trade_log)
    print(f"Backtest complete: {len(trade_log)} trades executed")

    return results, trades
