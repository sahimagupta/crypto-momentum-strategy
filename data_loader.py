import requests
import pandas as pd
from datetime import datetime, timedelta


def fetch_crypto_data(coin_id, vs_currency, days):
    """
    Fetch historical daily price data from CoinGecko API.
    Returns a DataFrame with date, open, high, low, close, volume.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "daily"
    }

    print(f"Fetching {days} days of {coin_id.upper()} data...")
    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}")

    data = response.json()

    # build dataframe from price data
    df = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    # add volume if available
    if "total_volumes" in data:
        vol_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
        vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
        vol_df.set_index("timestamp", inplace=True)
        df = df.join(vol_df, how="left")

    # add market cap
    if "market_caps" in data:
        cap_df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        cap_df["timestamp"] = pd.to_datetime(cap_df["timestamp"], unit="ms")
        cap_df.set_index("timestamp", inplace=True)
        df = df.join(cap_df, how="left")

    # drop any rows with missing close price
    df.dropna(subset=["close"], inplace=True)

    print(f"Loaded {len(df)} data points from {df.index[0].date()} to {df.index[-1].date()}")
    return df


def load_from_csv(filepath):
    """
    Load price data from a local CSV file.
    Expects columns: date, close (at minimum).
    """
    df = pd.read_csv(filepath, parse_dates=["date"], index_col="date")
    df.sort_index(inplace=True)
    return df
