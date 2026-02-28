"""
Strategy module.
Implements momentum-based moving average crossover signal generation.
"""

import pandas as pd
import numpy as np


def compute_indicators(df, short_window, long_window, momentum_period):
    """
    Compute technical indicators on price data.

    Calculates:
        - Simple Moving Averages (short and long)
        - Momentum (Rate of Change)
        - Bollinger Band width (for volatility context)
        - Daily returns

    Args:
        df: DataFrame with 'close' column
        short_window: period for short SMA
        long_window: period for long SMA
        momentum_period: lookback for ROC calculation

    Returns:
        DataFrame with indicator columns added
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    if len(df) < long_window:
        raise ValueError(
            f"Need at least {long_window} data points, got {len(df)}"
        )

    df = df.copy()

    # moving averages
    df["sma_short"] = df["close"].rolling(window=short_window, min_periods=short_window).mean()
    df["sma_long"] = df["close"].rolling(window=long_window, min_periods=long_window).mean()

    # momentum as rate of change (%)
    df["momentum"] = df["close"].pct_change(periods=momentum_period) * 100

    # bollinger bands (20-period, 2 std) for volatility measure
    bb_window = 20
    df["bb_mid"] = df["close"].rolling(window=bb_window).mean()
    bb_std = df["close"].rolling(window=bb_window).std()
    df["bb_upper"] = df["bb_mid"] + 2 * bb_std
    df["bb_lower"] = df["bb_mid"] - 2 * bb_std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]

    # volume moving average (for volume confirmation)
    if "volume" in df.columns:
        df["vol_ma"] = df["volume"].rolling(window=20).mean()
        df["vol_ratio"] = df["volume"] / df["vol_ma"]

    # daily returns
    df["daily_return"] = df["close"].pct_change()

    return df


def generate_signals(df, momentum_threshold=0):
    """
    Generate buy/sell signals using MA crossover with momentum filter.

    Entry conditions (go long):
        1. Short SMA crosses above Long SMA
        2. Momentum (ROC) is above threshold
        3. Volume is above average (if volume data available)

    Exit conditions:
        1. Short SMA crosses below Long SMA
        OR
        2. Momentum drops below threshold

    Signals are shifted by 1 day to avoid look-ahead bias
    (we see today's signal, execute tomorrow).

    Args:
        df: DataFrame with indicator columns from compute_indicators()
        momentum_threshold: minimum ROC value to confirm trend

    Returns:
        DataFrame with signal, position, and trade columns
    """
    required = ["sma_short", "sma_long", "momentum"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing indicator columns: {missing}. Run compute_indicators() first.")

    df = df.copy()

    # base signal: MA crossover + momentum confirmation
    ma_condition = df["sma_short"] > df["sma_long"]
    mom_condition = df["momentum"] > momentum_threshold

    # optional volume confirmation
    if "vol_ratio" in df.columns:
        vol_condition = df["vol_ratio"] > 0.8  # volume at least 80% of average
        df["signal"] = np.where(ma_condition & mom_condition & vol_condition, 1, 0)
    else:
        df["signal"] = np.where(ma_condition & mom_condition, 1, 0)

    # shift to avoid look-ahead bias
    df["position"] = df["signal"].shift(1)

    # identify trade entries and exits
    df["trade"] = df["position"].diff()

    # clean up NaN rows from rolling calculations
    df.dropna(subset=["position", "trade"], inplace=True)

    buy_count = (df["trade"] == 1).sum()
    sell_count = (df["trade"] == -1).sum()
    hold_days = (df["position"] == 1).sum()
    total_days = len(df)

    print(f"[+] Signals: {buy_count} buys, {sell_count} sells")
    print(f"[+] In market: {hold_days}/{total_days} days ({hold_days/total_days:.1%})")

    return df
