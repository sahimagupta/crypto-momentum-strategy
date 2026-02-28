import pandas as pd
import numpy as np


def compute_indicators(df, short_ma, long_ma, momentum_period):
    """
    Calculate moving averages and momentum indicator.
    
    Parameters:
        df: DataFrame with 'close' column
        short_ma: window for short moving average
        long_ma: window for long moving average
        momentum_period: lookback for rate of change
    
    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()

    # simple moving averages
    df["sma_short"] = df["close"].rolling(window=short_ma).mean()
    df["sma_long"] = df["close"].rolling(window=long_ma).mean()

    # momentum: rate of change (percentage)
    df["momentum"] = df["close"].pct_change(periods=momentum_period) * 100

    # daily returns for later analysis
    df["daily_return"] = df["close"].pct_change()

    return df


def generate_signals(df, momentum_threshold=0):
    """
    Generate trading signals based on MA crossover + momentum filter.
    
    Rules:
        BUY  (1): short MA > long MA AND momentum > threshold
        SELL (0): short MA < long MA OR momentum < threshold
    
    Returns:
        DataFrame with 'signal' and 'position' columns
    """
    df = df.copy()

    # raw signal: 1 when conditions met, 0 otherwise
    df["signal"] = 0
    mask = (df["sma_short"] > df["sma_long"]) & (df["momentum"] > momentum_threshold)
    df.loc[mask, "signal"] = 1

    # position: shifted signal (we act on next day's open)
    df["position"] = df["signal"].shift(1)

    # detect actual trade points (where position changes)
    df["trade"] = df["position"].diff()

    # drop rows where indicators aren't ready yet
    df.dropna(inplace=True)

    buy_count = len(df[df["trade"] == 1])
    sell_count = len(df[df["trade"] == -1])
    print(f"Signals generated: {buy_count} buys, {sell_count} sells")

    return df
