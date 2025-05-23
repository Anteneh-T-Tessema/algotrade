# Advanced Algorithmic Trading Bot

A comprehensive algorithmic trading bot for cryptocurrency trading on Binance, with support for multiple trading strategies and robust backtesting capabilities.

## Features

- **Multiple Trading Strategies**:
  - Scalping Strategy
  - Mean Reversion Strategy (Bollinger Bands, Z-Scores)
  - Trend Following Strategy (Moving Averages, MACD)
  - Grid Trading Strategy
  - Arbitrage Strategy (Triangular and Cross-Exchange)
  - Dollar-Cost Averaging (DCA) Strategy

- **Enhanced Backtesting Engine**:
  - Position tracking with P&L calculations
  - Detailed performance metrics (Sharpe, Sortino, Calmar ratios)
  - Drawdown monitoring and visualization
  - Walk-forward optimization
  - Multi-strategy comparison

- **Real-Time Trading**:
  - Live execution on Binance
  - Risk management with position sizing and stop-loss
  - Multiple timeframe analysis
  - Telegram notifications for trade alerts

- **Performance Dashboard**:
  - Interactive Streamlit web interface
  - Real-time performance monitoring
  - Trade history visualization
  - Equity curve and drawdown charts

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/botsalgo.git
   cd botsalgo
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Binance API keys:
   - Create a file named `.env` in the `config` directory
   - Add your API keys in the following format:
   ```
   API_KEY=your_binance_api_key
   API_SECRET=your_binance_api_secret
   ```

4. Configure your trading parameters in `config/config.yaml`

## Usage

### Running the Trading Bot

To start the live trading bot:

```bash
python bot.py
```

### Running Backtests

For a simple backtest:

```bash
python backtest.py --strategy scalping --symbol BTCUSDT --start-date 2023-01-01
```

For an advanced backtest with multiple strategies and enhanced metrics:

```bash
python advanced_backtest.py --strategy trend_following --symbol BTCUSDT --start-date 2023-01-01 --end-date 2023-12-31 --initial-capital 10000
```

### Testing All Strategies

To run comprehensive tests on all strategies with various market conditions:

```bash
python test_all_strategies.py
```

### Running the Performance Dashboard

To launch the interactive trading performance dashboard:

```bash
streamlit run dashboard.py
```

## Strategy Descriptions

### Scalping Strategy
Quick trades that capitalize on small price movements with tight stop-losses and take-profits. Uses RSI, Bollinger Bands, and volume spikes to identify entry and exit points.

### Mean Reversion Strategy
Trades based on the principle that prices tend to revert to their mean. Uses Bollinger Bands and Z-Scores to identify overbought and oversold conditions.

### Trend Following Strategy
Follows established market trends using moving average crossovers, MACD, and directional indicators (ADX). Aims to capture significant price movements in trending markets.

### Grid Trading Strategy
Places a grid of buy and sell orders at regular price intervals. Profits from price oscillations in ranging markets by buying low and selling high repeatedly.

### Arbitrage Strategy
Exploits price discrepancies between related assets or markets. Supports triangular arbitrage (between three currencies) and cross-exchange arbitrage (same asset on different exchanges).

### Dollar-Cost Averaging (DCA) Strategy
Systematically buys assets at regular intervals regardless of price, with enhancements for buying more on significant dips and using technical indicators to improve entry timing.

## Project Structure

```
botsalgo/
├── bot.py                  # Main trading bot
├── backtest.py             # Basic backtesting script
├── advanced_backtest.py    # Enhanced backtesting with comprehensive metrics
├── backtest_engine.py      # Sophisticated backtesting engine
├── test_all_strategies.py  # Script to test all strategies
├── dashboard.py            # Performance monitoring dashboard
├── config/                 # Configuration files
│   ├── config.yaml         # Bot configuration
│   └── .env                # API keys (create this file)
├── data/                   # Data storage
│   ├── plots/              # Generated charts
│   └── results/            # Backtest results
├── logs/                   # Log files
├── strategies/             # Trading strategies
│   ├── base_strategy.py    # Base strategy class
│   ├── scalping_strategy.py
│   ├── mean_reversion_strategy.py
│   ├── trend_following_strategy.py
│   ├── grid_trading_strategy.py
│   ├── arbitrage_strategy.py
│   └── dca_strategy.py
└── utils/                  # Utility functions
    ├── history_loader.py   # Historical data loading
    ├── indicators.py       # Technical indicators
    ├── logger.py           # Logging setup
    ├── risk_management.py  # Risk management tools
    └── telegram_notifications.py  # Telegram alerts
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.
