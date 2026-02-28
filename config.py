"""
Configuration for the backtester.
Modify these parameters to test different strategy variations.
"""

# --- Strategy Parameters ---
SHORT_MA = 20              # short moving average period (days)
LONG_MA = 50               # long moving average period (days)
MOMENTUM_PERIOD = 14       # rate of change lookback
MOMENTUM_THRESHOLD = 0     # min ROC to confirm entry

# --- Risk Management ---
INITIAL_CAPITAL = 10000    # starting portfolio value in USD
TRANSACTION_COST = 0.001   # 0.1% per trade (typical exchange fee)
STOP_LOSS = -0.05          # exit if position drops 5%

# --- Data Settings ---
COIN_ID = "bitcoin"        # coingecko coin id
VS_CURRENCY = "usd"
LOOKBACK_DAYS = 365        # historical data range

# --- Supported coins for multi-asset analysis ---
SUPPORTED_COINS = [
    "bitcoin",
    "ethereum",
    "solana",
    "cardano",
    "ripple",
]

# --- Output ---
OUTPUT_DIR = "output"
