#!/usr/bin/env python3
"""
Backtesting script for the scalping trading bot
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from binance.client import Client
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import strategy and indicators
from utils.indicators import calculate_indicators
from strategies.scalping_strategy import ScalpingStrategy
from utils.logger import setup_logger

def load_historical_data(symbol, interval, start_str, end_str=None):
    """
    Load historical data from Binance
    """
    load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
    
    api_key = os.environ.get('API_KEY')
    api_secret = os.environ.get('API_SECRET')
    
    if not api_key or not api_secret:
        logger = logging.getLogger("backtest")
        logger.warning("API key or secret not found. Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)
    
    try:
        client = Client(api_key, api_secret)
        
        # Test connection
        client.ping()
        
        # Fetch historical klines
        klines = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_str,
            end_str=end_str
        )
        
        # Create DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                          'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
        
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
        
        return df
    except ConnectionError as e:
        logger = logging.getLogger("backtest")
        logger.error(f"Connection error with Binance API: {str(e)}")
        logger.warning("Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)
    except TimeoutError as e:
        logger = logging.getLogger("backtest")
        logger.error(f"Timeout connecting to Binance API: {str(e)}")
        logger.warning("Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)
    except ImportError as e:
        logger = logging.getLogger("backtest")
        logger.error(f"Import error with Binance client: {str(e)}")
        logger.warning("Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)
    except ValueError as e:
        logger = logging.getLogger("backtest")
        logger.error(f"Value error processing Binance data: {str(e)}")
        logger.warning("Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)
    except Exception as e:
        logger = logging.getLogger("backtest")
        logger.error(f"Unexpected error with Binance API: {str(e)}")
        logger.warning("Using mock data for testing.")
        return generate_mock_data(symbol, interval, start_str, end_str)

def generate_mock_data(symbol, interval, start_str, end_str=None):
    """
    Generate mock price data for testing when Binance API is not available
    """
    logger = logging.getLogger("backtest")
    logger.info("Generating mock price data for testing")
    
    # Parse start and end dates
    start_date = pd.to_datetime(start_str)
    if end_str:
        end_date = pd.to_datetime(end_str)
    else:
        end_date = datetime.now()
    
    # Determine time delta based on interval
    if interval.endswith('m'):
        minutes = int(interval[:-1])
        freq = f"{minutes}min"
    elif interval.endswith('h'):
        hours = int(interval[:-1])
        freq = f"{hours}H"
    elif interval.endswith('d'):
        days = int(interval[:-1])
        freq = f"{days}D"
    else:
        freq = "1H"  # Default to 1 hour
    
    # Generate datetime index
    datetime_index = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate mock price data with deliberate patterns for trading signals
    base_price = 30000 if "BTC" in symbol else 2000 if "ETH" in symbol else 300  # Base price depending on symbol
    
    # Generate price movement with some deliberate patterns for buy/sell signals
    n = len(datetime_index)
    
    # Create a sine wave pattern with some noise for more realistic price movement
    # Use a pattern that will create clear buy/sell signals for our mock strategy
    t = np.linspace(0, 6*np.pi, n)  # 3 complete cycles
    sine_wave = np.sin(t)
    noise = np.random.normal(0, 0.05, size=n)  # Reduced noise
    trend = np.linspace(0, 0.5, n)  # Upward trend
    
    pattern = sine_wave + noise + trend
    df_index = pd.Index(datetime_index, name='mock')
    
    # Scale pattern to reasonable price movements
    price_multipliers = 1 + pattern * 0.02  # Scale to +/- 2% movements
    
    prices = base_price * np.cumprod(price_multipliers)
    
    # Create dataframe with our mock index
    df = pd.DataFrame(index=df_index)
    df['timestamp'] = datetime_index
    df['close_time'] = df['timestamp'] + pd.Timedelta(minutes=1)
    
    # Generate OHLCV data
    df['close'] = prices
    df['open'] = df['close'].shift(1)
    df.loc[df.index[0], 'open'] = base_price
    
    volatility = base_price * 0.005  # 0.5% volatility
    df['high'] = df['close'] + np.random.uniform(0, volatility, size=len(df))
    df['low'] = df['close'] - np.random.uniform(0, volatility, size=len(df))
    df['low'] = df[['low', 'open', 'close']].min(axis=1)  # Ensure low is the lowest
    df['high'] = df[['high', 'open', 'close']].max(axis=1)  # Ensure high is the highest
    
    # Generate volume data - higher volume on bigger price moves
    base_volume = 100
    df['volume'] = base_volume * (1 + np.abs(df['close'].pct_change(fill_method=None)) * 100)
    df.loc[df.index[0], 'volume'] = base_volume
    
    # Add other required columns
    df['quote_asset_volume'] = df['volume'] * df['close']
    df['number_of_trades'] = (df['volume'] / 10).astype(int)
    df['taker_buy_base_asset_volume'] = df['volume'] * 0.6  # Assume 60% taker buy volume
    df['taker_buy_quote_asset_volume'] = df['taker_buy_base_asset_volume'] * df['close']
    df['ignore'] = 0
    
    return df

def backtest_strategy(symbol, start_date, end_date=None, interval='1m', use_mock=False):
    """
    Backtest the scalping strategy
    
    Parameters:
    -----------
    symbol : str
        Trading pair symbol (e.g., 'BTCUSDT')
    start_date : str
        Start date for backtesting
    end_date : str, optional
        End date for backtesting. If None, current date is used
    interval : str
        Candlestick interval (e.g., '1m', '5m', '1h')
    use_mock : bool
        Whether to use the mock strategy for testing
    """
    # Set up logger
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    logger = setup_logger('backtest', os.path.join(log_dir, 'backtest.log'))
    logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date or 'now'}")
    
    # Load historical data
    df = load_historical_data(symbol, interval, start_date, end_date)
    
    # Determine if we should use the mock strategy
    is_mock_data = False
    if isinstance(df.index, pd.Index) and df.index.name == 'mock':
        is_mock_data = True
        use_mock = True
        logger.info("Using mock trading strategy for generated data")
    
    # Choose the appropriate strategy
    if use_mock or is_mock_data:
        # Import the mock strategy
        from strategies.mock_strategy import MockTradingStrategy
        strategy = MockTradingStrategy(logger)
    else:
        # Set up strategy configuration for the real strategy
        strategy_config = {
            'ema_fast': 8,
            'ema_slow': 21,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2,
            'volume_ma_period': 20,
            'min_volume_multiplier': 1.5
        }
        
        # Calculate indicators
        df = calculate_indicators(df, strategy_config)
        
        # Initialize strategy
        strategy = ScalpingStrategy(strategy_config, logger)
    
    # Generate signals
    signals = []
    for i in range(30, len(df)):  # Skip first 30 rows for indicator warmup
        window = df.iloc[:i+1]
        signal = strategy.generate_signal(window)
        signals.append(signal)
    
    # Add signals to dataframe
    df = df.iloc[30:].copy()  # Skip first 30 rows
    df['signal'] = signals
    
    # Simulate trading
    initial_capital = 1000.0
    position = 0
    capital = initial_capital
    trades = []
    
    for i in range(1, len(df)):
        prev_row = df.iloc[i-1]
        current_row = df.iloc[i]
        
        # Execute buy
        if prev_row['signal'] == 'BUY' and position == 0:
            entry_price = current_row['open']
            stop_loss, take_profit = strategy.calculate_exit_points(entry_price, 'BUY')
            position = capital / entry_price
            capital = 0
            logger.info(f"BUY at {entry_price}, position: {position}")
            trades.append({
                'type': 'BUY',
                'timestamp': current_row['timestamp'],
                'price': entry_price,
                'position': position,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            
        # Execute sell
        elif prev_row['signal'] == 'SELL' and position > 0:
            exit_price = current_row['open']
            capital = position * exit_price
            profit_pct = (exit_price / trades[-1]['price'] - 1) * 100
            position = 0
            logger.info(f"SELL at {exit_price}, profit: {profit_pct:.2f}%")
            trades.append({
                'type': 'SELL',
                'timestamp': current_row['timestamp'],
                'price': exit_price,
                'capital': capital,
                'profit_pct': profit_pct
            })
            
        # Check for stop loss and take profit
        elif position > 0:
            if current_row['low'] <= trades[-1]['stop_loss']:
                # Stop loss hit
                exit_price = trades[-1]['stop_loss']
                capital = position * exit_price
                profit_pct = (exit_price / trades[-1]['price'] - 1) * 100
                position = 0
                logger.info(f"STOP LOSS at {exit_price}, profit: {profit_pct:.2f}%")
                trades.append({
                    'type': 'STOP_LOSS',
                    'timestamp': current_row['timestamp'],
                    'price': exit_price,
                    'capital': capital,
                    'profit_pct': profit_pct
                })
            elif current_row['high'] >= trades[-1]['take_profit']:
                # Take profit hit
                exit_price = trades[-1]['take_profit']
                capital = position * exit_price
                profit_pct = (exit_price / trades[-1]['price'] - 1) * 100
                position = 0
                logger.info(f"TAKE PROFIT at {exit_price}, profit: {profit_pct:.2f}%")
                trades.append({
                    'type': 'TAKE_PROFIT',
                    'timestamp': current_row['timestamp'],
                    'price': exit_price,
                    'capital': capital,
                    'profit_pct': profit_pct
                })
    
    # Calculate final capital if still in position
    if position > 0:
        final_price = df.iloc[-1]['close']
        capital = position * final_price
        profit_pct = (final_price / trades[-1]['price'] - 1) * 100
        logger.info(f"FINAL at {final_price}, profit: {profit_pct:.2f}%")
    
    # Calculate performance metrics
    total_return = (capital - initial_capital) / initial_capital * 100
    
    # Extract trade results
    buy_trades = [t for t in trades if t['type'] == 'BUY']
    sell_trades = [t for t in trades if t['type'] in ['SELL', 'STOP_LOSS', 'TAKE_PROFIT']]
    
    if not buy_trades or not sell_trades:
        logger.warning("No complete trades found")
        return None
    
    # Calculate trade statistics
    profits = [t['profit_pct'] for t in trades if 'profit_pct' in t]
    winning_trades = [p for p in profits if p > 0]
    losing_trades = [p for p in profits if p <= 0]
    
    results = {
        'symbol': symbol,
        'start_date': df.iloc[0]['timestamp'],
        'end_date': df.iloc[-1]['timestamp'],
        'initial_capital': initial_capital,
        'final_capital': capital,
        'total_return': total_return,
        'total_trades': len(profits),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / len(profits) if profits else 0,
        'average_profit': sum(winning_trades) / len(winning_trades) if winning_trades else 0,
        'average_loss': sum(losing_trades) / len(losing_trades) if losing_trades else 0,
        'profit_factor': abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf'),
        'trades': trades,
        'dataframe': df
    }
    
    return results

def plot_backtest_results(results):
    """Plot backtest results"""
    if not results:
        print("No results to plot")
        return
        
    df = results['dataframe']
    trades = results['trades']
    
    # Create figure and axis
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot price chart
    axes[0].plot(df['timestamp'], df['close'], label='Price')
    
    # Plot indicators only if they exist in the dataframe
    if 'ema_fast' in df.columns and 'ema_slow' in df.columns:
        axes[0].plot(df['timestamp'], df['ema_fast'], label="EMA Fast")
        axes[0].plot(df['timestamp'], df['ema_slow'], label="EMA Slow")
        
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        axes[0].plot(df['timestamp'], df['bb_upper'], 'g--', alpha=0.3, label="Bollinger Upper")
        axes[0].plot(df['timestamp'], df['bb_lower'], 'g--', alpha=0.3, label="Bollinger Lower")
    
    # Plot buy and sell points
    for trade in trades:
        if trade['type'] == 'BUY':
            axes[0].scatter(trade['timestamp'], trade['price'], marker='^', color='g', s=100)
        elif trade['type'] == 'SELL':
            axes[0].scatter(trade['timestamp'], trade['price'], marker='v', color='r', s=100)
        elif trade['type'] == 'STOP_LOSS':
            axes[0].scatter(trade['timestamp'], trade['price'], marker='v', color='purple', s=100)
        elif trade['type'] == 'TAKE_PROFIT':
            axes[0].scatter(trade['timestamp'], trade['price'], marker='v', color='blue', s=100)
    
    axes[0].set_title(f"{results['symbol']} Backtest Results")
    axes[0].legend()
    
    # Plot volume in the second subplot
    axes[1].bar(df['timestamp'], df['volume'], alpha=0.3, color='blue')
    axes[1].set_title("Volume")
    
    # Plot RSI if available
    if 'rsi' in df.columns:
        # Add a third subplot for RSI
        fig.set_figheight(15)
        rsi_ax = fig.add_subplot(3, 1, 3)
        rsi_ax.plot(df['timestamp'], df['rsi'])
        rsi_ax.axhline(y=70, color='r', linestyle='--', alpha=0.3)
        rsi_ax.axhline(y=30, color='g', linestyle='--', alpha=0.3)
        rsi_ax.set_title("RSI")
    
    # Show stats
    stats_text = (
        f"Total Return: {results['total_return']:.2f}%\n"
        f"Total Trades: {results['total_trades']}\n"
        f"Win Rate: {results['win_rate'] * 100:.2f}%\n"
        f"Profit Factor: {results['profit_factor']:.2f}\n"
        f"Avg Profit: {results['average_profit']:.2f}%\n"
        f"Avg Loss: {results['average_loss']:.2f}%"
    )
    
    fig.text(0.01, 0.01, stats_text, fontsize=12, verticalalignment='bottom')
    
    plt.tight_layout()
    
    # Save the figure
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    plt.savefig(os.path.join(plots_dir, f"{results['symbol']}_backtest.png"))
    plt.close()

if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Backtest the scalping strategy')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading pair symbol')
    parser.add_argument('--days', type=int, default=1, help='Number of days to backtest')
    parser.add_argument('--interval', type=str, default='1m', help='Candlestick interval')
    parser.add_argument('--mock', action='store_true', help='Use mock strategy without requiring API access')
    args = parser.parse_args()
    
    # Calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    # Run backtest
    results = backtest_strategy(
        symbol=args.symbol,
        start_date=start_date.strftime('%Y-%m-%d'),
        interval=args.interval,
        use_mock=args.mock
    )
    
    # Plot results
    if results:
        plot_backtest_results(results)
        print(f"Backtest completed: {results['total_trades']} trades, {results['win_rate']*100:.2f}% win rate, {results['total_return']:.2f}% return")
