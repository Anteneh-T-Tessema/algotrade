#!/usr/bin/env python3
"""
Advanced Algorithmic Trading Bot for Binance
-------------------------------------------
This bot implements multiple trading strategies for cryptocurrency pairs on Binance:
1. Scalping Strategy
2. Mean Reversion Strategy
3. Trend Following Strategy
4. Grid Trading Strategy 
5. Arbitrage Strategy
6. Dollar-Cost Averaging Strategy

Features:
- Real-time data processing and technical analysis
- Risk management with position sizing and stop-loss
- Multiple timeframe analysis
- Telegram notifications for trade alerts
- Detailed logging and performance tracking
"""

import os
import sys
import time
import logging
import schedule
import yaml
import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime, timedelta
from binance.client import Client
# Import Binance exceptions
try:
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    # Define them manually if imports fail
    class BinanceAPIException(Exception):
        pass
    
    class BinanceOrderException(Exception):
        pass

# Define order constants
ORDER_TYPE_LIMIT = 'LIMIT'
ORDER_TYPE_MARKET = 'MARKET'
ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from utils.logger import setup_logger
from utils.indicators import calculate_indicators
from utils.risk_management import RiskManager
from utils.telegram_notifications import TelegramNotifier
from utils.history_loader import HistoryLoader

# Import strategies
from strategies.scalping_strategy import ScalpingStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_following_strategy import TrendFollowingStrategy
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.dca_strategy import DCAStrategy

class TradingBot:
    """Main trading bot class that orchestrates the entire trading process."""
    
    def __init__(self, config_path=None):
        """Initialize the trading bot with configuration."""
        # Set up base paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load environment variables
        load_dotenv(os.path.join(self.base_dir, 'config', '.env'))
        
        # Set up logging
        logs_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        self.logger = setup_logger('trading_bot', os.path.join(logs_dir, 'trading_bot.log'))
        self.logger.info("Initializing Trading Bot")
        
        # Load configuration
        self.config_path = config_path or os.path.join(self.base_dir, 'config', 'config.yaml')
        self.load_config()
        
        # Initialize Binance client
        self.initialize_client()
        
        # Initialize components
        self.risk_manager = RiskManager(self.config['risk_management'], self.logger)
        self.strategy = ScalpingStrategy(self.config['strategy'], self.logger)
        
        # Initialize notification system if enabled
        if self.config['general']['telegram_notifications']:
            self.notifier = TelegramNotifier(self.logger)
        else:
            self.notifier = None
        
        # Initialize trading state
        self.active_trades = {}
        self.trade_history = []
        self.last_prices = {}
        self.balance = {}
        
        self.logger.info("Trading Bot initialized successfully")
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            self.logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError as e:
            self.logger.error(f"Config file not found: {str(e)}")
            raise
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing config file: {str(e)}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in config file: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading config: {str(e)}")
            raise
    
    def initialize_client(self):
        """Initialize Binance API client."""
        try:
            api_key = os.environ.get('API_KEY')
            api_secret = os.environ.get('API_SECRET')
            
            if not api_key or not api_secret:
                self.logger.error("API key or secret not found in environment variables")
                raise ValueError("API credentials not found")
            
            if self.config['exchange']['testnet']:
                self.client = Client(api_key, api_secret, testnet=True)
                self.logger.info("Connected to Binance Testnet")
            else:
                self.client = Client(api_key, api_secret)
                self.logger.info("Connected to Binance Live")
                
            # Test connection
            server_time = self.client.get_server_time()
            self.logger.info(f"Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance client: {str(e)}")
            raise
    
    def update_market_data(self, symbol, timeframe, limit=100):
        """Fetch and update market data for a trading pair."""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=timeframe,
                limit=limit
            )
            
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
            
            # Calculate indicators
            df = calculate_indicators(df, self.config['strategy'])
            
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error for {symbol}: {str(e)}")
            return None
        except ConnectionError as e:
            self.logger.error(f"Connection error updating market data for {symbol}: {str(e)}")
            return None
        except TimeoutError as e:
            self.logger.error(f"Timeout updating market data for {symbol}: {str(e)}")
            return None
        except ValueError as e:
            self.logger.error(f"Value error processing data for {symbol}: {str(e)}")
            return None
        except KeyError as e:
            self.logger.error(f"Key error in market data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error updating market data for {symbol}: {str(e)}")
            return None
    
    def update_account_balance(self):
        """Update account balance information."""
        try:
            account = self.client.get_account()
            self.balance = {asset['asset']: float(asset['free']) for asset in account['balances']}
            self.logger.info(f"Account balance updated")
            return self.balance
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error updating account balance: {str(e)}")
            return None
        except ConnectionError as e:
            self.logger.error(f"Connection error updating account balance: {str(e)}")
            return None
        except KeyError as e:
            self.logger.error(f"Key error processing account data: {str(e)}")
            return None
        except TypeError as e:
            self.logger.error(f"Type error processing account data: {str(e)}")
            return None
        except ValueError as e:
            self.logger.error(f"Value error processing account data: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error updating account balance: {str(e)}")
            return None
    
    def execute_order(self, symbol, side, quantity, order_type=ORDER_TYPE_MARKET, price=None, stop_price=None):
        """Execute an order on Binance."""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
            }
            
            if price is not None:
                params['price'] = price
                
            if stop_price is not None:
                params['stopPrice'] = stop_price
                
            if self.config['exchange']['testnet']:
                self.logger.info(f"[TEST] Executing order: {params}")
                # Simulate order response in testnet
                return {
                    'orderId': f"test_{int(time.time())}",
                    'symbol': symbol,
                    'side': side,
                    'type': order_type,
                    'status': 'FILLED',
                    'price': price or self.last_prices.get(symbol, 0),
                    'executedQty': quantity,
                    'time': int(time.time() * 1000)
                }
            else:
                order = self.client.create_order(**params)
                self.logger.info(f"Order executed: {order}")
                
                # Notify if enabled
                if self.notifier:
                    self.notifier.send_order_notification(order)
                    
                return order
                
        except BinanceAPIException as e:
            self.logger.error(f"API error executing order on {symbol}: {e}")
            if self.notifier:
                self.notifier.send_error_notification(f"API error: {e}")
            return None
            
        except BinanceOrderException as e:
            self.logger.error(f"Order error on {symbol}: {e}")
            if self.notifier:
                self.notifier.send_error_notification(f"Order error: {e}")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error executing order on {symbol}: {e}")
            if self.notifier:
                self.notifier.send_error_notification(f"Unexpected error: {e}")
            return None
    
    def place_buy_order(self, symbol, quantity):
        """Place a buy order."""
        pair_config = next((pair for pair in self.config['trading_pairs'] if pair['symbol'] == symbol), None)
        if not pair_config:
            self.logger.error(f"No configuration found for {symbol}")
            return None
        
        # Round quantity to the appropriate precision
        quantity = round(quantity, pair_config['quantity_precision'])
        
        return self.execute_order(
            symbol=symbol,
            side=SIDE_BUY,
            quantity=quantity
        )
    
    def place_sell_order(self, symbol, quantity):
        """Place a sell order."""
        pair_config = next((pair for pair in self.config['trading_pairs'] if pair['symbol'] == symbol), None)
        if not pair_config:
            self.logger.error(f"No configuration found for {symbol}")
            return None
            
        # Round quantity to the appropriate precision
        quantity = round(quantity, pair_config['quantity_precision'])
        
        return self.execute_order(
            symbol=symbol,
            side=SIDE_SELL,
            quantity=quantity
        )
    
    def place_stop_loss(self, symbol, quantity, stop_price):
        """Place a stop loss order."""
        pair_config = next((pair for pair in self.config['trading_pairs'] if pair['symbol'] == symbol), None)
        if not pair_config:
            self.logger.error(f"No configuration found for {symbol}")
            return None
            
        # Round values to appropriate precision
        quantity = round(quantity, pair_config['quantity_precision'])
        stop_price = round(stop_price, pair_config['price_precision'])
        
        return self.execute_order(
            symbol=symbol,
            side=SIDE_SELL,
            quantity=quantity,
            order_type=ORDER_TYPE_STOP_LOSS,
            stop_price=stop_price
        )
    
    def analyze_pair(self, symbol):
        """Analyze a trading pair and decide on trading actions."""
        try:
            # Get trading pair config
            pair_config = next((pair for pair in self.config['trading_pairs'] if pair['symbol'] == symbol), None)
            if not pair_config:
                self.logger.error(f"No configuration found for {symbol}")
                return
                
            # Update market data
            df = self.update_market_data(symbol, self.config['strategy']['timeframe'])
            if df is None or df.empty:
                self.logger.warning(f"No data available for {symbol}")
                return
                
            # Store last price
            self.last_prices[symbol] = df['close'].iloc[-1]
            
            # Check if we can trade based on risk management
            if not self.risk_manager.can_open_new_trade(symbol, self.active_trades):
                self.logger.info(f"Risk management prevented new trade for {symbol}")
                return
                
            # Get trading signals from strategy
            signal = self.strategy.generate_signal(df)
            
            # Execute trades based on signals
            if signal == 'BUY':
                # Calculate position size
                balance_quote = self.balance.get(pair_config['quote_asset'], 0)
                allocation = balance_quote * pair_config['allocation']
                
                if allocation < 10:  # Minimum 10 USDT equivalent
                    self.logger.info(f"Insufficient funds for {symbol}")
                    return
                    
                price = df['close'].iloc[-1]
                quantity = allocation / price
                
                # Ensure minimum quantity
                if quantity < pair_config['min_quantity']:
                    self.logger.info(f"Calculated quantity below minimum for {symbol}")
                    return
                
                # Place buy order
                buy_order = self.place_buy_order(symbol, quantity)
                
                if buy_order:
                    # Record the trade
                    trade_id = f"{symbol}_{buy_order['orderId']}"
                    self.active_trades[trade_id] = {
                        'symbol': symbol,
                        'entry_price': float(buy_order.get('price', price)),
                        'quantity': float(buy_order['executedQty']),
                        'entry_time': datetime.now(),
                        'stop_loss_price': price * (1 - self.config['risk_management']['stop_loss_percentage'] / 100),
                        'take_profit_price': price * (1 + self.config['risk_management']['take_profit_percentage'] / 100),
                        'status': 'OPEN'
                    }
                    
                    self.logger.info(f"Opened new trade for {symbol} at {price}")
                    
            elif signal == 'SELL':
                # Check if we have any open trades for this symbol
                symbol_trades = {k: v for k, v in self.active_trades.items() 
                               if v['symbol'] == symbol and v['status'] == 'OPEN'}
                
                if not symbol_trades:
                    # We don't have positions to sell
                    return
                    
                for trade_id, trade in symbol_trades.items():
                    # Place sell order
                    sell_order = self.place_sell_order(symbol, trade['quantity'])
                    
                    if sell_order:
                        # Update trade record
                        sell_price = float(sell_order.get('price', df['close'].iloc[-1]))
                        profit = (sell_price - trade['entry_price']) * trade['quantity']
                        profit_pct = ((sell_price / trade['entry_price']) - 1) * 100
                        
                        trade['exit_price'] = sell_price
                        trade['exit_time'] = datetime.now()
                        trade['profit'] = profit
                        trade['profit_percentage'] = profit_pct
                        trade['status'] = 'CLOSED'
                        
                        # Move to history
                        self.trade_history.append(trade)
                        del self.active_trades[trade_id]
                        
                        self.logger.info(f"Closed trade for {symbol} at {sell_price}, profit: {profit_pct:.2f}%")
                        
        except KeyError as e:
            self.logger.error(f"Key error analyzing {symbol}: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Value error analyzing {symbol}: {str(e)}")
        except TypeError as e:
            self.logger.error(f"Type error analyzing {symbol}: {str(e)}")
        except IndexError as e:
            self.logger.error(f"Index error analyzing {symbol}: {str(e)}")
        except AttributeError as e:
            self.logger.error(f"Attribute error analyzing {symbol}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error analyzing {symbol}: {str(e)}")
    
    def manage_open_trades(self):
        """Check and manage open trades for stop loss and take profit."""
        if not self.active_trades:
            return
            
        for trade_id, trade in list(self.active_trades.items()):
            symbol = trade['symbol']
            current_price = self.last_prices.get(symbol)
            
            if not current_price:
                continue
                
            # Check for stop loss
            if current_price <= trade['stop_loss_price']:
                self.logger.info(f"Stop loss triggered for {symbol} at {current_price}")
                sell_order = self.place_sell_order(symbol, trade['quantity'])
                
                if sell_order:
                    # Update trade record
                    sell_price = float(sell_order.get('price', current_price))
                    profit = (sell_price - trade['entry_price']) * trade['quantity']
                    profit_pct = ((sell_price / trade['entry_price']) - 1) * 100
                    
                    trade['exit_price'] = sell_price
                    trade['exit_time'] = datetime.now()
                    trade['profit'] = profit
                    trade['profit_percentage'] = profit_pct
                    trade['status'] = 'CLOSED'
                    trade['exit_reason'] = 'STOP_LOSS'
                    
                    # Move to history
                    self.trade_history.append(trade)
                    del self.active_trades[trade_id]
                    
                    if self.notifier:
                        self.notifier.send_trade_notification(
                            f"❌ Stop loss hit on {symbol}\n"
                            f"Profit: {profit_pct:.2f}%\n"
                            f"Entry: {trade['entry_price']}\n"
                            f"Exit: {sell_price}"
                        )
            
            # Check for take profit
            elif current_price >= trade['take_profit_price']:
                self.logger.info(f"Take profit triggered for {symbol} at {current_price}")
                sell_order = self.place_sell_order(symbol, trade['quantity'])
                
                if sell_order:
                    # Update trade record
                    sell_price = float(sell_order.get('price', current_price))
                    profit = (sell_price - trade['entry_price']) * trade['quantity']
                    profit_pct = ((sell_price / trade['entry_price']) - 1) * 100
                    
                    trade['exit_price'] = sell_price
                    trade['exit_time'] = datetime.now()
                    trade['profit'] = profit
                    trade['profit_percentage'] = profit_pct
                    trade['status'] = 'CLOSED'
                    trade['exit_reason'] = 'TAKE_PROFIT'
                    
                    # Move to history
                    self.trade_history.append(trade)
                    del self.active_trades[trade_id]
                    
                    if self.notifier:
                        self.notifier.send_trade_notification(
                            f"✅ Take profit hit on {symbol}\n"
                            f"Profit: {profit_pct:.2f}%\n"
                            f"Entry: {trade['entry_price']}\n"
                            f"Exit: {sell_price}"
                        )
                        
            # Check for trailing stop if activated
            elif (self.config['risk_management'].get('trailing_stop_activation') and 
                  current_price >= trade['entry_price'] * (1 + self.config['risk_management']['trailing_stop_activation'] / 100)):
                
                # Only update stop loss if the new one would be higher
                new_stop_loss = current_price * (1 - self.config['risk_management']['trailing_stop_distance'] / 100)
                if new_stop_loss > trade['stop_loss_price']:
                    old_stop = trade['stop_loss_price']
                    trade['stop_loss_price'] = new_stop_loss
                    self.logger.info(f"Updated trailing stop for {symbol} from {old_stop} to {new_stop_loss}")
    
    def run_trading_cycle(self):
        """Run a complete trading cycle."""
        try:
            self.logger.info("Starting trading cycle")
            
            # Update account balance
            self.update_account_balance()
            
            # Analyze each trading pair
            for pair_config in self.config['trading_pairs']:
                symbol = pair_config['symbol']
                self.analyze_pair(symbol)
                
            # Manage open trades
            self.manage_open_trades()
            
            self.logger.info("Trading cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Trading cycle error: {str(e)}")
    
    def save_trading_history(self):
        """Save trading history to a CSV file."""
        if not self.trade_history:
            return
            
        try:
            df = pd.DataFrame(self.trade_history)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Ensure data directory exists
            data_dir = os.path.join(self.base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Save file with proper path
            filename = os.path.join(data_dir, f"trade_history_{timestamp}.csv")
            df.to_csv(filename, index=False)
            self.logger.info(f"Trading history saved to {filename}")
        except PermissionError as e:
            self.logger.error(f"Permission error saving trading history: {str(e)}")
        except FileNotFoundError as e:
            self.logger.error(f"File path error saving trading history: {str(e)}")
        except IOError as e:
            self.logger.error(f"IO error saving trading history: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Value error saving trading history: {str(e)}")
        except TypeError as e:
            self.logger.error(f"Type error saving trading history: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error saving trading history: {str(e)}")
    
    def start(self):
        """Start the trading bot."""
        try:
            self.logger.info("Starting trading bot")
            
            if self.notifier:
                self.notifier.send_notification("🚀 Trading bot started")
                
            # Set up schedules
            schedule.every(1).minutes.do(self.run_trading_cycle)
            schedule.every(1).hours.do(self.save_trading_history)
            
            # Initial run
            self.run_trading_cycle()
            
            # Main loop
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
            if self.notifier:
                self.notifier.send_notification("⏹ Trading bot stopped by user")
                
        except ImportError as e:
            self.logger.error(f"Import error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Bot import error: {str(e)}")
                
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Binance API error: {str(e)}")
                
        except ConnectionError as e:
            self.logger.error(f"Connection error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Connection error: {str(e)}")
                
        except AttributeError as e:
            self.logger.error(f"Attribute error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Bot attribute error: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            if self.notifier:
                self.notifier.send_error_notification(f"Bot crashed: {str(e)}")
                
        finally:
            # Save final trading history
            self.save_trading_history()


if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
