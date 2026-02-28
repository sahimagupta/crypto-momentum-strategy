# Strategy parameters
SHORT_MA = 20          # short moving average window (days)
LONG_MA = 50           # long moving average window (days)
MOMENTUM_PERIOD = 14   # rate of change lookback period
MOMENTUM_THRESHOLD = 0 # minimum ROC to confirm trend

# Backtest settings
INITIAL_CAPITAL = 10000
TRANSACTION_COST = 0.001  # 0.1% per trade (exchange fee)

# Data settings
COIN_ID = "bitcoin"
VS_CURRENCY = "usd"
LOOKBACK_DAYS = 365    # 1 year of historical data

# Output
OUTPUT_DIR = "output"
