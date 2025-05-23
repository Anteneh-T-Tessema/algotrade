#!/usr/bin/env python3
"""
History Loader

This module is responsible for loading and managing historical market data.
It supports:
- Loading data from Binance API
- Loading data from local CSV files
- Generating mock data for testing
- Preprocessing and cleaning market data
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv
import logging

class HistoryLoader:
    """
    Handles loading and managing historical market data from various sources
    """
    
    def __init__(self, logger=None):
        """Initialize the history loader with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of Binance client."""
        if self._client is None:
            try:
                # Load environment variables
                load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', '.env'))
                
                api_key = os.environ.get('API_KEY')
                api_secret = os.environ.get('API_SECRET')
                
                if not api_key or not api_secret:
                    self.logger.warning("API key or secret not found in environment variables")
                    return None
                
                self._client = Client(api_key, api_secret)
                self.logger.info("Binance client initialized successfully")
                
            except ImportError as e:
                self.logger.error(f"Missing required library: {str(e)}")
                return None
            except ValueError as e:
                self.logger.error(f"Invalid API credentials: {str(e)}")
                return None
            except ConnectionError as e:
                self.logger.error(f"Connection error initializing Binance client: {str(e)}")
                return None
            except Exception as e:
                self.logger.error(f"Failed to initialize Binance client: {str(e)}")
                return None
                
        return self._client
    
    def load_historical_data(self, symbol, interval, start_str, end_str=None, use_mock=False):
        """
        Load historical market data from Binance API or generate mock data.
        
        Parameters:
        -----------
        symbol : str
            Trading pair symbol (e.g., 'BTCUSDT')
        interval : str
            Candlestick interval (e.g., '1m', '5m', '1h')
        start_str : str
            Start date string (e.g., '1 day ago', '2021-01-01')
        end_str : str, optional
            End date string. If None, current time is used.
        use_mock : bool, optional
            Whether to generate mock data instead of fetching from Binance.
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing historical market data
        """
        if use_mock:
            self.logger.info(f"Generating mock data for {symbol} ({interval}) from {start_str} to {end_str or 'now'}")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
            
        if self.client is None:
            self.logger.warning("Binance client not available. Using mock data.")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
            
        try:
            self.logger.info(f"Fetching {symbol} ({interval}) data from {start_str} to {end_str or 'now'}")
            
            # Fetch historical klines from Binance
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str
            )
            
            if not klines:
                self.logger.warning(f"No data returned from Binance for {symbol}. Using mock data.")
                return self.generate_mock_data(symbol, interval, start_str, end_str)
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Process the data
            return self._process_dataframe(df)
            
        except ConnectionError as e:
            self.logger.error(f"Connection error fetching data from Binance: {str(e)}")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
        except ValueError as e:
            self.logger.error(f"Value error fetching data from Binance: {str(e)}")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
        except TypeError as e:
            self.logger.error(f"Type error fetching data from Binance: {str(e)}")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
        except Exception as e:
            self.logger.error(f"Error fetching data from Binance: {str(e)}")
            return self.generate_mock_data(symbol, interval, start_str, end_str)
    
    def _process_dataframe(self, df):
        """
        Process raw dataframe from Binance API into a clean format.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Raw dataframe from Binance API
            
        Returns:
        --------
        pandas.DataFrame
            Processed dataframe
        """
        # Convert timestamp columns
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # Convert numeric columns
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_asset_volume', 'number_of_trades',
                          'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
        
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
        
        # Set index
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def generate_mock_data(self, symbol, interval, start_str, end_str=None):
        """
        Generate mock market data for testing.
        
        Parameters:
        -----------
        symbol : str
            Trading pair symbol (e.g., 'BTCUSDT')
        interval : str
            Candlestick interval (e.g., '1m', '5m', '1h')
        start_str : str
            Start date string
        end_str : str, optional
            End date string. If None, current time is used.
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing mock market data
        """
        # Parse start and end dates
        if isinstance(start_str, str):
            if start_str.endswith('ago'):
                # Handle relative time formats (e.g., "1 day ago")
                parts = start_str.split()
                if len(parts) >= 3 and parts[1] in ['day', 'days', 'hour', 'hours', 'minute', 'minutes']:
                    count = int(parts[0])
                    unit = parts[1].rstrip('s')  # Remove plural 's'
                    
                    if unit == 'day':
                        start_date = datetime.now() - timedelta(days=count)
                    elif unit == 'hour':
                        start_date = datetime.now() - timedelta(hours=count)
                    elif unit == 'minute':
                        start_date = datetime.now() - timedelta(minutes=count)
                    else:
                        start_date = datetime.now() - timedelta(days=1)
                else:
                    # Default to 1 day ago if format not recognized
                    start_date = datetime.now() - timedelta(days=1)
            else:
                # Try to parse as date string
                try:
                    start_date = pd.to_datetime(start_str)
                except:
                    start_date = datetime.now() - timedelta(days=1)
        else:
            start_date = datetime.now() - timedelta(days=1)
            
        if end_str:
            try:
                end_date = pd.to_datetime(end_str)
            except:
                end_date = datetime.now()
        else:
            end_date = datetime.now()
        
        # Determine time delta based on interval
        if interval.endswith('m'):
            minutes = int(interval[:-1])
            freq = f"{minutes}min"
        elif interval.endswith('h'):
            hours = int(interval[:-1])
            freq = f"{hours}h"
        elif interval.endswith('d'):
            days = int(interval[:-1])
            freq = f"{days}d"
        else:
            freq = "1h"  # Default to 1 hour
        
        # Generate datetime index
        datetime_index = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Set seed for reproducibility
        np.random.seed(42)
        
        # Generate price data based on the symbol
        if 'BTC' in symbol:
            base_price = 30000
            volatility = 0.02
        elif 'ETH' in symbol:
            base_price = 2000
            volatility = 0.03
        elif 'BNB' in symbol:
            base_price = 300
            volatility = 0.025
        else:
            base_price = 100
            volatility = 0.01

        # Number of data points
        n = len(datetime_index)
        
        # Generate price movement with deliberate patterns for testing strategies
        # Create a sine wave with trend for directionality and noise for realism
        t = np.linspace(0, 6*np.pi, n)  # 3 complete cycles
        
        # Add a trend component for mean reversion testing
        trend = np.linspace(0, 0.5, n)
        
        # Base sine wave with various frequencies
        sine_wave1 = np.sin(t)
        sine_wave2 = 0.5 * np.sin(2.5*t)  # Higher frequency
        
        # Create pattern with realistic market behavior
        pattern = sine_wave1 + sine_wave2 + trend + np.random.normal(0, 0.05, n)
        
        # Scale pattern to reasonable price movements
        pattern = pattern * volatility
        
        # Generate cumulative price changes
        price_multipliers = np.cumprod(1 + pattern)
        prices = base_price * price_multipliers
        
        # Create DataFrame
        df = pd.DataFrame(index=datetime_index)
        df.index.name = 'timestamp'
        
        # OHLC data
        df['close'] = prices
        df['open'] = np.roll(df['close'], 1)
        df.loc[df.index[0], 'open'] = base_price
        
        # High and low with realistic ranges based on volatility
        candle_range = prices * volatility * 0.5
        df['high'] = df['close'] + np.abs(np.random.normal(0, 1, n)) * candle_range
        df['low'] = df['close'] - np.abs(np.random.normal(0, 1, n)) * candle_range
        
        # Ensure high is highest and low is lowest within each candle
        for i in range(len(df)):
            highest = max(df['open'].iloc[i], df['close'].iloc[i], df['high'].iloc[i])
            lowest = min(df['open'].iloc[i], df['close'].iloc[i], df['low'].iloc[i])
            df.loc[df.index[i], 'high'] = highest
            df.loc[df.index[i], 'low'] = lowest
        
        # Volume data - higher on trend changes
        df['volume'] = 100 * (1 + 2 * np.abs(np.diff(pattern, prepend=0)) + 0.5 * np.random.random(n))
        
        # Additional columns for compatibility with Binance data
        df['close_time'] = df.index + pd.Timedelta(minutes=1)
        df['quote_asset_volume'] = df['volume'] * df['close']
        df['number_of_trades'] = (df['volume'] / 10).astype(int) + 10
        df['taker_buy_base_asset_volume'] = df['volume'] * 0.6
        df['taker_buy_quote_asset_volume'] = df['taker_buy_base_asset_volume'] * df['close']
        df['ignore'] = 0
        
        return df
    
    def save_to_csv(self, df, symbol, interval, directory='data'):
        """
        Save historical data to CSV file.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing market data
        symbol : str
            Trading pair symbol
        interval : str
            Candlestick interval
        directory : str
            Directory to save the file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{symbol}_{interval}_{timestamp}.csv"
        filepath = os.path.join(directory, filename)
        
        # Save to CSV
        df.to_csv(filepath)
        self.logger.info(f"Data saved to {filepath}")
        
        return filepath
    
    def load_from_csv(self, filepath):
        """
        Load historical data from CSV file.
        
        Parameters:
        -----------
        filepath : str
            Path to the CSV file
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing historical market data
        """
        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            self.logger.info(f"Data loaded from {filepath}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data from {filepath}: {str(e)}")
            return None
