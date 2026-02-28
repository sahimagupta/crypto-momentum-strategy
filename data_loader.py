"""
Data loading module.
Handles fetching historical crypto data from CoinGecko API
and loading from local CSV files.
"""

import requests
import pandas as pd
import time
import os


class DataLoadError(Exception):
    """Raised when data fetching or loading fails."""
    pass


def fetch_crypto_data(coin_id, vs_currency, days, retries=3):
    """
    Fetch historical daily price data from CoinGecko free API.

    Args:
        coin_id: coingecko coin identifier (e.g. 'bitcoin')
        vs_currency: quote currency (e.g. 'usd')
        days: number of days to look back
        retries: number of retry attempts on failure

    Returns:
        pd.DataFrame with columns: close, volume, market_cap
        Index is datetime
    
    Raises:
        DataLoadError: if API fails after all retries
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "daily"
    }

    print(f"[*] Fetching {days} days of {coin_id.upper()} data...")

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                # rate limited - wait and retry
                wait = 10 * attempt
                print(f"[!] Rate limited. Waiting {wait}s before retry...")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                raise DataLoadError(
                    f"API returned status {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            break

        except requests.exceptions.Timeout:
            print(f"[!] Request timed out (attempt {attempt}/{retries})")
            if attempt == retries:
                raise DataLoadError("API request timed out after all retries")
            time.sleep(5)

        except requests.exceptions.ConnectionError:
            print(f"[!] Connection error (attempt {attempt}/{retries})")
            if attempt == retries:
                raise DataLoadError("Could not connect to CoinGecko API")
            time.sleep(5)

    # parse prices
    if "prices" not in data or len(data["prices"]) == 0:
        raise DataLoadError(f"No price data returned for {coin_id}")

    df = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    # parse volumes
    if "total_volumes" in data:
        vol_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
        vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
        vol_df.set_index("timestamp", inplace=True)
        df = df.join(vol_df, how="left")

    # parse market caps
    if "market_caps" in data:
        cap_df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        cap_df["timestamp"] = pd.to_datetime(cap_df["timestamp"], unit="ms")
        cap_df.set_index("timestamp", inplace=True)
        df = df.join(cap_df, how="left")

    df.dropna(subset=["close"], inplace=True)

    if len(df) < 60:
        raise DataLoadError(
            f"Not enough data points ({len(df)}). Need at least 60 for indicators."
        )

    print(f"[+] Loaded {len(df)} data points: {df.index[0].date()} to {df.index[-1].date()}")
    return df


def load_from_csv(filepath):
    """
    Load price data from a local CSV file as fallback.

    Expected CSV format:
        date,close,volume (header row required)

    Args:
        filepath: path to CSV file

    Returns:
        pd.DataFrame indexed by date

    Raises:
        DataLoadError: if file not found or format is wrong
    """
    if not os.path.exists(filepath):
        raise DataLoadError(f"File not found: {filepath}")

    try:
        df = pd.read_csv(filepath, parse_dates=["date"], index_col="date")
    except (KeyError, ValueError) as e:
        raise DataLoadError(f"CSV format error: {e}. Expected columns: date, close")

    if "close" not in df.columns:
        raise DataLoadError("CSV must have a 'close' column")

    df.sort_index(inplace=True)
    df.dropna(subset=["close"], inplace=True)

    print(f"[+] Loaded {len(df)} rows from {filepath}")
    return df
