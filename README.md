# Crypto Momentum Strategy Backtester

A simple momentum-based trading strategy backtester for cryptocurrency markets. Fetches historical price data and tests a dual moving average crossover strategy with momentum confirmation.

## Strategy Logic

- **Entry Signal (Long):** Short-term MA crosses above long-term MA AND momentum (rate of change) is positive
- **Exit Signal:** Short-term MA crosses below long-term MA OR momentum turns negative
- **Universe:** BTC/USDT (easily extendable to other pairs)

## How It Works

1. Fetches daily OHLCV data from CoinGecko (free, no API key needed)
2. Computes moving averages (20-day and 50-day) and momentum (ROC)
3. Generates buy/sell signals based on crossover + momentum filter
4. Simulates portfolio performance with transaction costs
5. Outputs key metrics: total return, Sharpe ratio, max drawdown, win rate

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Output

- Performance summary printed to console
- output/equity_curve.png - portfolio value over time
- output/signals.png - price chart with buy/sell markers
- output/results.csv - daily returns and positions

## Project Structure

`
main.py              # Entry point
data_loader.py       # Fetch and clean market data
strategy.py          # Signal generation logic
backtester.py        # Portfolio simulation engine
utils.py             # Helper functions (metrics, plotting)
config.py            # Strategy parameters
requirements.txt
output/              # Generated charts and results
`

## Parameters (config.py)

- SHORT_MA = 20 (Short moving average window)
- LONG_MA = 50 (Long moving average window)
- MOMENTUM_PERIOD = 14 (Rate of change lookback)
- TRANSACTION_COST = 0.001 (0.1% per trade)
- INITIAL_CAPITAL = 10000 (Starting portfolio value)

## Notes

- This is a research/educational project, not financial advice
- Past performance does not guarantee future results
- Strategy uses daily timeframe data
