#!/usr/bin/env python3
"""
Dollar-Cost Averaging (DCA) Strategy

This strategy buys assets at regular intervals regardless of price,
with optional enhancements like buying more on dips or market weakness.
"""

from strategies.base_strategy import Strategy, PositionSide
import pandas as pd
import numpy as np
import logging
from datetime import timedelta


class DCAStrategy(Strategy):
    """
    Dollar-Cost Averaging Strategy with enhancements for buying on dips
    """
    
    def __init__(self, name="DCA", params=None):
        """
        Initialize the strategy with parameters
        
        Parameters:
        -----------
        name : str
            Strategy name
        params : dict, optional
            Strategy parameters including:
            - interval_hours: Hours between regular purchases
            - buy_amount: Amount in USD to buy at each interval
            - dip_threshold_pct: Buy extra on dips of this percentage
            - dip_multiplier: Multiply regular buy amount by this on dips
            - use_rsi: Use RSI for detecting oversold conditions
            - rsi_period: RSI calculation period
            - rsi_oversold: RSI oversold threshold
            - rsi_multiplier: Multiply buy amount when RSI is oversold
            - take_profit_pct: Take profit at this percentage gain
            - max_positions: Maximum number of positions to hold
            - merge_positions: Whether to merge positions or track separately
            
        Raises:
        -------
        ValueError
            If any parameter is invalid
        """
        default_params = {
            'interval_hours': 24,       # Hours between regular purchases
            'buy_amount': 100,          # Amount in USD to buy at each interval
            'dip_threshold_pct': 5.0,   # Buy extra on dips of this percentage
            'dip_multiplier': 1.5,      # Multiply regular buy amount by this on dips
            'use_rsi': True,            # Use RSI for detecting oversold conditions
            'rsi_period': 14,           # RSI calculation period
            'rsi_oversold': 30,         # RSI oversold threshold
            'rsi_multiplier': 1.3,      # Multiply buy amount when RSI is oversold
            'take_profit_pct': 20.0,    # Take profit at this percentage gain
            'max_positions': 10,        # Maximum number of positions to hold
            'merge_positions': True     # Whether to merge positions or track separately
        }
        
        # Override default params with any provided ones
        self.params = {**default_params, **(params or {})}
        
        # Setup logger early for validation error logging
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Validate parameters
        try:
            self._validate_parameters()
        except ValueError as e:
            self.logger.error(f"Parameter validation error: {str(e)}")
            raise
        
        super().__init__(name, self.params)
        
        # DCA-specific attributes
        self.last_purchase_time = None
        self.positions = []  # List of all positions (if not merging)
        self.average_entry = None
        self.total_investment = 0
        self.total_position_size = 0
        
    def _validate_parameters(self):
        """
        Validate strategy parameters
        
        Raises:
        -------
        ValueError
            If any parameter is invalid
        """
        # Validate numeric parameters are positive
        positive_params = [
            'interval_hours', 'buy_amount', 'dip_threshold_pct', 
            'dip_multiplier', 'rsi_period', 'rsi_multiplier',
            'take_profit_pct', 'max_positions'
        ]
        
        for param in positive_params:
            if self.params[param] <= 0:
                raise ValueError(f"Parameter '{param}' must be positive. Got: {self.params[param]}")
        
        # Validate RSI parameters
        if not isinstance(self.params['use_rsi'], bool):
            raise ValueError(f"Parameter 'use_rsi' must be a boolean. Got: {self.params['use_rsi']}")
            
        if not 0 <= self.params['rsi_oversold'] <= 100:
            raise ValueError(f"RSI oversold threshold must be between 0 and 100. Got: {self.params['rsi_oversold']}")
            
        # Validate merge_positions is a boolean
        if not isinstance(self.params['merge_positions'], bool):
            raise ValueError(f"Parameter 'merge_positions' must be a boolean. Got: {self.params['merge_positions']}")
            
        # Validate RSI period is an integer
        if not isinstance(self.params['rsi_period'], int):
            raise ValueError(f"RSI period must be an integer. Got: {self.params['rsi_period']}")
            
        # Validate max positions is an integer
        if not isinstance(self.params['max_positions'], int):
            raise ValueError(f"Max positions must be an integer. Got: {self.params['max_positions']}")
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for DCA strategy
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with added technical indicators
            
        Raises:
        -------
        ValueError
            If input data is invalid
        """
        try:
            # Check if dataframe is empty
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to calculate_indicators")
                return df
                
            # Validate dataframe has required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in dataframe: {missing_columns}")
                
            # Make a copy to avoid modifying the original
            result = df.copy()
            
            # Calculate RSI if needed
            if self.params['use_rsi']:
                try:
                    rsi_period = self.params['rsi_period']
                    
                    # Handle case where we don't have enough data for RSI
                    if len(result) < rsi_period + 1:
                        self.logger.warning(
                            f"Not enough data for RSI calculation. Need at least {rsi_period+1} candles, got {len(result)}"
                        )
                        # Continue but RSI will have NaN values for the initial periods
                    
                    # Calculate price changes
                    delta = result['close'].diff()
                    
                    # Separate gains and losses
                    gain = delta.copy()
                    loss = delta.copy()
                    gain[gain < 0] = 0
                    loss[loss > 0] = 0
                    loss = abs(loss)
                    
                    # Calculate average gain and loss
                    avg_gain = gain.rolling(window=rsi_period).mean()
                    avg_loss = loss.rolling(window=rsi_period).mean()
                    
                    # Calculate relative strength with protection against division by zero
                    rs = avg_gain / (avg_loss + 1e-10)  # Add small value to prevent division by zero
                    
                    # Calculate RSI
                    result['rsi'] = 100 - (100 / (1 + rs))
                    
                    # Ensure RSI values are within bounds [0, 100]
                    result['rsi'] = result['rsi'].clip(0, 100)
                    
                except Exception as e:
                    self.logger.error(f"Error calculating RSI: {str(e)}")
                    # Add a column of NaN to prevent errors when the indicator is referenced
                    result['rsi'] = np.nan
            
            try:
                # Calculate percentage change from previous day's close
                result['pct_change'] = result['close'].pct_change(fill_method=None) * 100
            except Exception as e:
                self.logger.error(f"Error calculating percentage change: {str(e)}")
                result['pct_change'] = np.nan
            
            try:
                # Calculate moving average for reference
                ma_period = 20  # Hard-coded for now, could be a parameter
                
                # Check if we have enough data for the moving average
                if len(result) < ma_period:
                    self.logger.warning(
                        f"Not enough data for MA calculation. Need {ma_period} periods, got {len(result)}"
                    )
                    # Continue but MA will have NaN values
                
                result['ma20'] = result['close'].rolling(window=ma_period).mean()
                
                # Calculate dip indicator (current price vs MA)
                # Protect against division by zero
                result['dip_from_ma'] = result.apply(
                    lambda x: (x['close'] / x['ma20'] - 1) * 100 if x['ma20'] > 0 else np.nan, 
                    axis=1
                )
            except KeyError as e:
                self.logger.error(f"KeyError calculating moving averages: Missing key {str(e)}")
                result['ma20'] = np.nan
                result['dip_from_ma'] = np.nan
            except ValueError as e:
                self.logger.error(f"ValueError calculating moving averages: {str(e)}")
                result['ma20'] = np.nan
                result['dip_from_ma'] = np.nan
            except TypeError as e:
                self.logger.error(f"TypeError calculating moving averages: {str(e)}")
                result['ma20'] = np.nan
                result['dip_from_ma'] = np.nan
            
            try:
                # Calculate percentage drawdown from recent peak
                result['rolling_max'] = result['close'].rolling(window=20).max()
                
                # Protect against division by zero
                result['drawdown'] = result.apply(
                    lambda x: (x['close'] / x['rolling_max'] - 1) * 100 if x['rolling_max'] > 0 else np.nan,
                    axis=1
                )
            except KeyError as e:
                self.logger.error(f"KeyError calculating drawdown: Missing key {str(e)}")
                result['rolling_max'] = np.nan
                result['drawdown'] = np.nan
            except ValueError as e:
                self.logger.error(f"ValueError calculating drawdown: {str(e)}")
                result['rolling_max'] = np.nan
                result['drawdown'] = np.nan
            except TypeError as e:
                self.logger.error(f"TypeError calculating drawdown: {str(e)}")
                result['rolling_max'] = np.nan
                result['drawdown'] = np.nan
            
            return result
            
        except KeyError as e:
            self.logger.error(f"KeyError calculating indicators: Missing key {str(e)}")
            # Return the original dataframe to avoid breaking the pipeline
            return df
        except ValueError as e:
            self.logger.error(f"ValueError calculating indicators: {str(e)}")
            # Return the original dataframe to avoid breaking the pipeline
            return df
        except TypeError as e:
            self.logger.error(f"TypeError calculating indicators: {str(e)}")
            # Return the original dataframe to avoid breaking the pipeline
            return df
        except AttributeError as e:
            self.logger.error(f"AttributeError calculating indicators: {str(e)}")
            # Return the original dataframe to avoid breaking the pipeline
            return df
    
    def generate_signal(self, df):
        """
        Generate trading signals based on DCA strategy
        
        For DCA, we simply check if it's time for the next purchase,
        with additional signals for dip buying.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data and indicators
            
        Returns:
        --------
        str
            'BUY', 'BUY_DIP', 'BUY_RSI', or 'HOLD' signal
            
        Raises:
        -------
        ValueError
            If input data is invalid
        """
        try:
            # Check if we have enough data
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to generate_signal")
                return 'HOLD'
            
            # Validate dataframe has required column
            if 'close' not in df.columns:
                raise ValueError("DataFrame is missing 'close' column")
            
            try:
                # Get the most recent candle
                current = df.iloc[-1]
                current_time = current.name if hasattr(current, 'name') else pd.Timestamp.now()
            except IndexError as e:
                self.logger.error(f"IndexError accessing candle data: {str(e)}")
                return 'HOLD'
            except AttributeError as e:
                self.logger.error(f"AttributeError accessing candle data: {str(e)}")
                return 'HOLD'
            
            # Check if we have all required indicators
            required_columns = ['pct_change', 'ma20', 'dip_from_ma', 'drawdown']
            if self.params['use_rsi']:
                required_columns.append('rsi')
                
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.info(f"Missing indicators: {missing_columns}. Calculating now.")
                try:
                    df = self.calculate_indicators(df)
                    current = df.iloc[-1]
                except KeyError as e:
                    self.logger.error(f"KeyError calculating missing indicators: {str(e)}")
                    return 'HOLD'
                except ValueError as e:
                    self.logger.error(f"ValueError calculating missing indicators: {str(e)}")
                    return 'HOLD'
                except IndexError as e:
                    self.logger.error(f"IndexError calculating missing indicators: {str(e)}")
                    return 'HOLD'
                except TypeError as e:
                    self.logger.error(f"TypeError calculating missing indicators: {str(e)}")
                    return 'HOLD'
                    return 'HOLD'
            
            # If this is our first run, set last purchase time
            if self.last_purchase_time is None:
                self.logger.info("Initializing DCA strategy with first purchase")
                self.last_purchase_time = current_time - timedelta(hours=self.params['interval_hours'] - 1)
                return 'BUY'  # Make an initial purchase
            
            # Check if it's time for a regular DCA purchase
            hours_since_last = 0
            try:
                if isinstance(current_time, pd.Timestamp) and isinstance(self.last_purchase_time, pd.Timestamp):
                    time_diff = current_time - self.last_purchase_time
                    hours_since_last = time_diff.total_seconds() / 3600
                else:
                    # Handle the case where timestamps are not comparable
                    self.logger.warning(
                        f"Time comparison issue: current_time: {type(current_time)}, last_purchase_time: {type(self.last_purchase_time)}"
                    )
                    # Try to convert to timestamps if they're not already
                    if not isinstance(current_time, pd.Timestamp):
                        current_time = pd.Timestamp(current_time)
                    if not isinstance(self.last_purchase_time, pd.Timestamp):
                        self.last_purchase_time = pd.Timestamp(self.last_purchase_time)
                    
                    time_diff = current_time - self.last_purchase_time
                    hours_since_last = time_diff.total_seconds() / 3600
            except Exception as e:
                self.logger.error(f"Error calculating time difference: {str(e)}")
                # Default to no time passed to be safe
                hours_since_last = 0
            
            # Check for regular interval purchase
            if hours_since_last >= self.params['interval_hours']:
                self.logger.info(f"DCA interval reached: {hours_since_last:.1f} hours since last purchase")
                
                try:
                    # Check if we should buy more on a dip
                    dip_threshold = self.params['dip_threshold_pct']
                    
                    # Safely check drawdown value
                    if pd.notna(current.get('drawdown')) and current['drawdown'] <= -dip_threshold:
                        self.logger.info(f"Dip detected: {current['drawdown']:.2f}% drawdown")
                        return 'BUY_DIP'  # Buy more on significant dip
                    elif (self.params['use_rsi'] and pd.notna(current.get('rsi')) and 
                          current['rsi'] <= self.params['rsi_oversold']):
                        self.logger.info(f"Oversold condition detected: RSI = {current['rsi']:.2f}")
                        return 'BUY_RSI'  # Buy more when oversold
                    else:
                        return 'BUY'  # Regular DCA purchase
                except Exception as e:
                    self.logger.error(f"Error determining buy signal: {str(e)}")
                    # Fall back to regular purchase when in doubt
                    return 'BUY'
            
            # Check for extra purchase on significant dip (even if not at regular interval)
            try:
                # Safely check for deep dips
                if (pd.notna(current.get('drawdown')) and 
                    current['drawdown'] <= -self.params['dip_threshold_pct'] * 1.5):  # Deeper dip than threshold
                    # Make sure we don't buy too frequently on dips
                    if hours_since_last >= self.params['interval_hours'] / 2:
                        self.logger.info(f"Deep dip detected: {current['drawdown']:.2f}% drawdown")
                        return 'BUY_DIP'
            except Exception as e:
                self.logger.error(f"Error checking for deep dips: {str(e)}")
                    
            return 'HOLD'
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {str(e)}")
            return 'HOLD'  # Default to HOLD on error
    
    def on_candle(self, candle, balance):
        """
        Process a new candle and determine DCA actions
        
        Parameters:
        -----------
        candle : pandas.Series
            A single candle with OHLCV data
        balance : float
            Current account balance
            
        Returns:
        --------
        dict or None
            Trade action to take, or None if no action
            Example: {'action': 'BUY', 'price': 100, 'size': 1}
            
        Raises:
        -------
        ValueError
            If input data is invalid
        """
        try:
            # Validate inputs
            if candle is None:
                raise ValueError("Candle data is None")
                
            if balance < 0:
                self.logger.warning(f"Invalid balance: {balance}. Must be non-negative.")
                balance = 0
                
            # Check required fields in candle
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in candle:
                    raise ValueError(f"Candle data missing required field: {field}")
            
            # Convert Series to DataFrame for indicator calculation if needed
            try:
                df = pd.DataFrame([candle])
                df = self.calculate_indicators(df)
                
                if df is None or df.empty:
                    raise ValueError("Failed to calculate indicators")
                    
                candle = df.iloc[0]
            except Exception as e:
                self.logger.error(f"Error calculating indicators in on_candle: {str(e)}")
                return None
            
            # Get current time
            try:
                current_time = candle.name if hasattr(candle, 'name') else pd.Timestamp.now()
            except Exception as e:
                self.logger.error(f"Error getting current time: {str(e)}")
                current_time = pd.Timestamp.now()
            
            # Generate signal
            try:
                signal = self.generate_signal(df)
            except Exception as e:
                self.logger.error(f"Error generating signal: {str(e)}")
                return None
            
            # Get current price
            try:
                current_price = candle['close']
                
                # Validate price
                if current_price <= 0:
                    raise ValueError(f"Invalid price: {current_price}")
            except Exception as e:
                self.logger.error(f"Error getting current price: {str(e)}")
                return None
            
            # Check if we've hit our take profit target
            try:
                if self.average_entry is not None and self.average_entry > 0:
                    current_profit_pct = (current_price / self.average_entry - 1) * 100
                    
                    if current_profit_pct >= self.params['take_profit_pct']:
                        # Sell all positions
                        if self.total_position_size > 0:
                            self.logger.info(
                                f"Take profit triggered: {current_profit_pct:.2f}% profit reached (target: {self.params['take_profit_pct']}%)"
                            )
                            return {
                                'action': 'SELL',
                                'price': current_price,
                                'size': self.total_position_size,
                                'reason': 'TAKE_PROFIT'
                            }
            except Exception as e:
                self.logger.error(f"Error checking take profit condition: {str(e)}")
            
            # Execute DCA logic
            if signal in ['BUY', 'BUY_DIP', 'BUY_RSI']:
                try:
                    # Determine buy amount
                    buy_amount = self.params['buy_amount']
                    
                    if signal == 'BUY_DIP':
                        buy_amount *= self.params['dip_multiplier']
                        self.logger.info(f"DIP DETECTED: Increasing buy amount to {buy_amount}")
                    elif signal == 'BUY_RSI':
                        buy_amount *= self.params['rsi_multiplier']
                        self.logger.info(f"OVERSOLD DETECTED: Increasing buy amount to {buy_amount}")
                    
                    # Check if we have enough balance
                    if buy_amount > balance:
                        self.logger.warning(f"Insufficient balance for DCA purchase: {balance} < {buy_amount}")
                        buy_amount = balance if balance > 0 else 0
                    
                    # Skip if buy amount is too small
                    if buy_amount < 0.01:
                        self.logger.warning(f"Buy amount too small: {buy_amount}. Skipping purchase.")
                        return None
                    
                    # Calculate position size
                    size = buy_amount / current_price
                    
                    # Update last purchase time
                    self.last_purchase_time = current_time
                    
                    # Update average entry price and total investment
                    if self.average_entry is None:
                        self.average_entry = current_price
                        self.total_investment = buy_amount
                        self.total_position_size = size
                    else:
                        # Calculate new average entry price
                        total_value = self.total_investment + buy_amount
                        total_size = self.total_position_size + size
                        self.average_entry = total_value / total_size
                        self.total_investment = total_value
                        self.total_position_size = total_size
                    
                    # Log the purchase decision
                    self.logger.info(
                        f"DCA purchase: {signal} at ${current_price:.2f}, size: {size:.6f}, "
                        f"avg entry: ${self.average_entry:.2f}, total invested: ${self.total_investment:.2f}"
                    )
                    
                    # Return action
                    return {
                        'action': 'BUY',
                        'price': current_price,
                        'size': size,
                        'dca': True,
                        'dca_type': signal,
                        'average_entry': self.average_entry,
                        'total_investment': self.total_investment
                    }
                except Exception as e:
                    self.logger.error(f"Error executing DCA buy logic: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing candle: {str(e)}")
            return None
    
    def calculate_exit_points(self, entry_price, side='BUY'):
        """
        Calculate exit points (stop loss and take profit) for a position
        
        For DCA, we typically don't use stop losses, but we do use take profit targets.
        
        Parameters:
        -----------
        entry_price : float
            Entry price of the position
        side : str
            Position side ('BUY' or 'SELL')
            
        Returns:
        --------
        tuple
            (stop_loss_price, take_profit_price)
            
        Raises:
        -------
        ValueError
            If entry price is invalid
        """
        try:
            # Validate input
            if entry_price is None:
                raise ValueError("Entry price is None")
                
            if not isinstance(entry_price, (int, float)):
                raise ValueError(f"Entry price must be a number. Got: {type(entry_price)}")
                
            if entry_price <= 0:
                raise ValueError(f"Entry price must be positive. Got: {entry_price}")
                
            if side not in ['BUY', 'SELL']:
                self.logger.warning(f"Invalid side: {side}. Must be 'BUY' or 'SELL'. Defaulting to 'BUY'.")
                side = 'BUY'
            
            # For DCA, we don't use stop loss
            stop_loss = None
            
            # Take profit at specified percentage
            take_profit_pct = self.params['take_profit_pct'] / 100
            
            if side == 'BUY':
                take_profit = entry_price * (1 + take_profit_pct)
            else:
                # For short positions (rarely used in DCA but included for completeness)
                take_profit = entry_price * (1 - take_profit_pct)
            
            self.logger.info(f"Exit points calculated: Stop loss: None, Take profit: ${take_profit:.2f}")
            return stop_loss, take_profit
            
        except Exception as e:
            self.logger.error(f"Error calculating exit points: {str(e)}")
            # Return safe defaults
            if side == 'BUY':
                # Conservative take profit at 10% above entry
                return None, entry_price * 1.1
            else:
                # Conservative take profit at 10% below entry
                return None, entry_price * 0.9
