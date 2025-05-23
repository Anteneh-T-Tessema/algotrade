# Advanced Algorithmic Trading Bot for Binance

An advanced, multi-strategy cryptocurrency trading bot for Binance that implements various trading strategies, advanced backtesting capabilities, and performance analytics.

## Features

- **Multiple Trading Strategies**:
  - **Scalping**: Exploits small price gaps using short-term trades with tight stop-loss
  - **Mean Reversion**: Trades on the assumption that prices will return to the mean after deviation
  - **Trend Following**: Identifies and rides directional market trends
  - **Grid Trading**: Places buy and sell orders at regular intervals around a set price
  - **Arbitrage**: Exploits price differences between markets
  - **Dollar-Cost Averaging (DCA)**: Systematically invests fixed amounts at regular intervals

- **Advanced Backtesting**:
  - Historical data analysis with realistic fee modeling
  - Detailed performance metrics (Sharpe ratio, drawdown, win rate)
  - Position tracking and equity curve generation
  - Multi-timeframe analysis

- **Performance Dashboard**:
  - Interactive visualization with Streamlit
  - Real-time monitoring of trading performance
  - Customizable charts and metrics
  - Strategy comparison tools

- **Risk Management**:
  - Position sizing based on volatility
  - Dynamic stop-loss and take-profit levels
  - Maximum drawdown protection
  - Portfolio correlation analysis

- **Automated Deployment**:
  - Market condition analysis
  - Optimal strategy selection
  - Parameter optimization
  - Testnet/mainnet switching

- **Notifications**:
  - Real-time trade alerts via Telegram
  - Error and performance notifications
  - Daily summary reports

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/advanced-trading-bot.git
cd advanced-trading-bot
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the config directory with the following content:

```env
API_KEY=your_binance_api_key
API_SECRET=your_binance_api_secret
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 4. Update configuration

Modify `config/config.yaml` with your trading preferences and risk parameters.

## Usage

### Running the Trading Bot

```bash
python bot.py
```

### Backtesting a Strategy

```bash
python advanced_backtest.py --strategy trend_following --symbol BTCUSDT --timeframe 1h --period 30d
```

### Testing All Strategies

```bash
python test_all_strategies.py
```

### Launching the Performance Dashboard

```bash
streamlit run dashboard.py
```

### Deploying the Optimal Strategy

```bash
# Analyze market and recommend strategy without deployment
python deploy.py --analyze

# Deploy with automatically selected best strategy (test mode)
python deploy.py

# Deploy with specific strategy (test mode)
python deploy.py --strategy trend_following

# Deploy with automatically selected best strategy in live mode
python deploy.py --live

# Run strategy tests before deployment
python deploy.py --test-strategies
```

## Strategy Details

### Scalping Strategy

A short-term trading strategy that aims to profit from small price movements. Parameters include:

- `rsi_length`: RSI indicator period
- `rsi_overbought`: Threshold for overbought conditions
- `rsi_oversold`: Threshold for oversold conditions

### Mean Reversion Strategy

Capitalizes on the tendency of prices to return to their mean. Uses:

- Bollinger Bands or Z-Score for identifying price extremes
- Optimized entry and exit points based on historical volatility

### Trend Following Strategy

Identifies and follows market trends. Features:

- Multiple moving averages for trend confirmation
- Volume-weighted trend signals
- Dynamic trailing stops for maximizing profits in strong trends

### Grid Trading Strategy

Places buy and sell orders at pre-defined intervals. Ideal for:

- Sideways/ranging markets
- Capturing regular price oscillations
- Generating returns in low-volatility environments

### Arbitrage Strategy

Exploits price differences between markets. Includes:

- Triangular arbitrage (between three currencies)
- Exchange arbitrage (same asset on different exchanges)
- Statistical arbitrage (pairs trading)

### Dollar-Cost Averaging Strategy

Systematic investment approach that reduces impact of volatility:

- Regular fixed-amount purchases
- Automated rebalancing options
- Long-term accumulation focus

## Project Structure

```
botsalgo/
├── advanced_backtest.py       # Enhanced backtest engine with detailed metrics
├── backtest_engine.py         # Core backtesting engine
├── backtest.py                # Simple backtest script
├── bot.py                     # Main trading bot
├── dashboard.py               # Interactive performance dashboard
├── deploy.py                  # Deployment script for optimal strategy
├── test_all_strategies.py     # Strategy testing across market conditions
├── test_bot.py                # Bot testing utilities
├── requirements.txt           # Project dependencies
├── config/                    # Configuration files
│   ├── config.yaml            # Main configuration
│   └── .env                   # Environment variables (API keys)
├── data/                      # Data storage
│   └── plots/                 # Generated charts and visualizations
├── logs/                      # Log files
├── strategies/                # Trading strategies
│   ├── arbitrage_strategy.py
│   ├── base_strategy.py       # Strategy interface
│   ├── dca_strategy.py
│   ├── grid_trading_strategy.py
│   ├── mean_reversion_strategy.py
│   ├── scalping_strategy.py
│   └── trend_following_strategy.py
└── utils/                     # Utility functions
    ├── history_loader.py      # Historical data retrieval
    ├── indicators.py          # Technical indicators
    ├── logger.py              # Logging setup
    ├── risk_management.py     # Risk management tools
    └── telegram_notifications.py # Notification system
```

## License

[MIT License](LICENSE)

## Disclaimer

This software is for educational purposes only. Use it at your own risk. The authors are not responsible for any financial losses incurred by using this software. Cryptocurrency trading involves substantial risk and is not suitable for all investors.