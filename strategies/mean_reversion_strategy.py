#!/usr/bin/env python3
"""
Mean Reversion Strategy

This strategy uses Bollinger Bands or Z-Score to identify mean reversion opportunities.
Mean reversion is based on the assumption that prices will tend to move back toward
their historical average after moving away from it.

The strategy can be configured to use either:
1. Bollinger Bands - Buy when price drops below lower band, sell when it rises above upper band
2. Z-Score - Buy when Z-score is below negative threshold (oversold), sell when it crosses back 
   above exit threshold

Key Parameters:
- lookback_period: Period for calculating mean and standard deviation
- entry_z_score: Z-score threshold for entry
- exit_z_score: Z-score threshold for exit
- use_bollinger: Whether to use Bollinger Bands instead of raw Z-score
- bollinger_std: Number of standard deviations for Bollinger Bands
"""

from strategies.base_strategy import Strategy, PositionSide
import pandas as pd
import numpy as np
import logging
import traceback


class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy using Bollinger Bands or Z-Score
    
    This strategy identifies when prices have moved significantly away from their
    historical average and trades on the assumption they will revert to the mean.
    """
    
    def __init__(self, name="MeanReversion", params=None):
        """
        Initialize the mean reversion strategy with parameters
        
        Parameters
        ----------
        name : str
            Strategy name identifier
        params : dict, optional
            Dictionary of strategy parameters that will override defaults
            
        Attributes
        ----------
        params : dict
            Complete set of strategy parameters (defaults + overrides)
        logger : logging.Logger
            Logger for this strategy instance
        """
        default_params = {
            'lookback_period': 20,       # Period for calculating mean and standard deviation
            'entry_z_score': 2.0,        # Z-score threshold for entry
            'exit_z_score': 0.0,         # Z-score threshold for exit
            'stop_loss_percentage': 2.0, # Stop loss percentage
            'take_profit_percentage': 4.0, # Take profit percentage
            'use_bollinger': True,       # Use Bollinger Bands instead of raw Z-score
            'bollinger_std': 2.0,        # Standard deviations for Bollinger Bands
            'max_positions': 1,          # Maximum positions allowed
            'position_size_pct': 95.0    # Position size as percentage of available capital
        }
        
        # Override default params with any provided ones
        self.params = {**default_params, **(params or {})}
        
        # Validate parameters
        self._validate_parameters()
        
        super().__init__(name, self.params)
        self.logger = logging.getLogger(f"strategy.{name}")
        self.logger.info(f"Initialized {name} strategy with parameters: {self.params}")
    
    def _validate_parameters(self):
        """
        Validate strategy parameters to ensure they're within acceptable ranges
        
        Raises
        ------
        ValueError
            If any parameter is invalid or out of acceptable range
        """
        try:
            # Ensure lookback period is reasonable
            if self.params['lookback_period'] < 2:
                self.params['lookback_period'] = 2
                logging.warning("Lookback period too small, setting to minimum value of 2")
                
            # Ensure z-score thresholds are reasonable
            if self.params['entry_z_score'] <= 0:
                self.params['entry_z_score'] = 2.0
                logging.warning("Entry Z-score must be positive, setting to default 2.0")
                
            # Ensure Bollinger band standard deviation is positive
            if self.params['bollinger_std'] <= 0:
                self.params['bollinger_std'] = 2.0
                logging.warning("Bollinger standard deviation must be positive, setting to default 2.0")
                
            # Ensure risk parameters are reasonable    
            if self.params['stop_loss_percentage'] <= 0 or self.params['stop_loss_percentage'] > 50:
                self.params['stop_loss_percentage'] = 2.0
                logging.warning("Stop loss percentage must be between 0-50, setting to default 2.0")
                
            if self.params['take_profit_percentage'] <= 0 or self.params['take_profit_percentage'] > 100:
                self.params['take_profit_percentage'] = 4.0
                logging.warning("Take profit percentage must be between 0-100, setting to default 4.0")
                
            if self.params['position_size_pct'] <= 0 or self.params['position_size_pct'] > 100:
                self.params['position_size_pct'] = 95.0
                logging.warning("Position size percentage must be between 0-100, setting to default 95.0")
                
        except KeyError as e:
            logging.error(f"Missing parameter: {str(e)}")
            # Fall back to default parameters if validation fails
            raise ValueError(f"Missing strategy parameter: {str(e)}")
        except TypeError as e:
            logging.error(f"Parameter type error: {str(e)}")
            # Fall back to default parameters if validation fails
            raise ValueError(f"Invalid parameter type: {str(e)}")
        except Exception as e:
            logging.error(f"Error validating parameters: {str(e)}")
            # Fall back to default parameters if validation fails
            raise ValueError(f"Invalid strategy parameters: {str(e)}")
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for mean reversion strategy
        
        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame with OHLCV price data
            
        Returns
        -------
        pandas.DataFrame
            DataFrame with added technical indicators:
            - ma: Moving average of closing prices
            - std: Standard deviation of closing prices
            - z_score: How many standard deviations price is from mean
            - bb_upper: Upper Bollinger Band (if use_bollinger=True)
            - bb_lower: Lower Bollinger Band (if use_bollinger=True)
        """
        try:
            # Check if dataframe is empty or invalid
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to calculate_indicators")
                return df
                
            # Check if 'close' column exists
            if 'close' not in df.columns:
                self.logger.error("DataFrame missing 'close' column in calculate_indicators")
                return df
                
            # Make a copy to avoid modifying the original
            result = df.copy()
            
            # Get lookback period from parameters
            lookback = self.params['lookback_period']
            
            # Check if we have enough data for indicators
            if len(result) < lookback:
                self.logger.warning(
                    f"Not enough data points for indicators: {len(result)} available, {lookback} required"
                )
                # Still calculate indicators but results will have NaN values
            
            # Calculate moving average
            result['ma'] = result['close'].rolling(window=lookback).mean()
            
            # Calculate standard deviation with safety check
            result['std'] = result['close'].rolling(window=lookback).std()
            
            # Handle zero standard deviation cases
            zero_std_mask = result['std'] == 0
            if zero_std_mask.any():
                # Substitute small value where std is zero
                min_std = result['close'].mean() * 0.0001 or 0.0001
                result.loc[zero_std_mask, 'std'] = min_std
                self.logger.warning(f"Zero standard deviation detected, using minimum value: {min_std}")
            
            # Calculate Z-score (how many standard deviations price is from mean)
            # Adding a small value to avoid division by zero
            result['z_score'] = (result['close'] - result['ma']) / (result['std'] + 1e-10)
            
            # Calculate Bollinger Bands if specified
            if self.params['use_bollinger']:
                bb_std = self.params['bollinger_std']
                result['bb_upper'] = result['ma'] + (result['std'] * bb_std)
                result['bb_lower'] = result['ma'] - (result['std'] * bb_std)
                
            return result
            
        except KeyError as e: # Handles missing columns in DataFrame
            self.logger.error(f"KeyError calculating indicators: Missing key {str(e)}")
            self.logger.error(traceback.format_exc())
            return df
        except ValueError as e: # Handles issues with data values (e.g. during calculations)
            self.logger.error(f"ValueError calculating indicators: {str(e)}")
            self.logger.error(traceback.format_exc())
            return df
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError calculating indicators: {str(e)}")
            self.logger.error(traceback.format_exc())
            return df
        except AttributeError as e: # Handles issues with method calls on incorrect types
            self.logger.error(f"AttributeError calculating indicators: {str(e)}")
            self.logger.error(traceback.format_exc())
            return df
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            self.logger.error(traceback.format_exc())
            # Return original dataframe if calculation fails
            return df
    
    def generate_signal(self, df):
        """
        Generate trading signals based on mean reversion indicators
        
        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame with OHLCV data and technical indicators
            
        Returns
        -------
        str
            Trading signal: 'BUY', 'SELL', or 'HOLD'
        """
        try:
            # Check if we have enough data
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to generate_signal")
                return 'HOLD'
                
            if len(df) < self.params['lookback_period'] + 1:
                self.logger.debug(f"Not enough data to generate signal: {len(df)} available, {self.params['lookback_period'] + 1} required")
                return 'HOLD'
            
            # Get the most recent candle
            try:
                current = df.iloc[-1]
            except IndexError as e:
                self.logger.error(f"Error accessing latest candle: {str(e)}")
                return 'HOLD'
            
            # Check if we have all required indicators
            required_columns = ['ma', 'std', 'z_score']
            if self.params['use_bollinger']:
                required_columns.extend(['bb_upper', 'bb_lower'])
                
            if not all(col in df.columns for col in required_columns):
                self.logger.debug("Missing indicators, recalculating...")
                df = self.calculate_indicators(df)
                try:
                    current = df.iloc[-1]
                except IndexError:
                    self.logger.error("Failed to access recalculated dataframe")
                    return 'HOLD'
            
            # Don't trade until we have enough data for indicators (non-NaN values)
            if pd.isna(current['ma']) or pd.isna(current['std']) or pd.isna(current['z_score']):
                self.logger.debug("Indicators contain NaN values, waiting for more data")
                return 'HOLD'
                
            # Check for extreme values that might indicate data issues
            if abs(current['z_score']) > 10:  # Extremely unlikely in normal markets
                self.logger.warning(f"Extreme z-score detected: {current['z_score']:.2f}")
                if abs(current['z_score']) > 20:  # Almost certainly a data issue
                    self.logger.error(f"Invalid z-score detected: {current['z_score']:.2f}, skipping signal generation")
                    return 'HOLD'
            
            # Generate signals using either Bollinger Bands or Z-score
            if self.params['use_bollinger']:
                # Bollinger Band strategy:
                # - Buy when price crosses below lower band
                # - Sell when price crosses above upper band or returns to mean
                
                # Define the conditions for entry and exit
                price_below_lower = current['close'] < current['bb_lower']
                price_above_upper = current['close'] > current['bb_upper']
                price_at_mean = abs(current['close'] - current['ma']) < (0.1 * current['std'])
                
                # Check if we have an open position
                if self.current_position is None:
                    # Entry signal for long positions
                    if price_below_lower:
                        return 'BUY'
                else:
                    # Exit signal for long positions
                    if price_above_upper or price_at_mean:
                        return 'SELL'
                        
            else:
                # Z-score strategy:
                # - Buy when Z-score is below negative threshold (oversold)
                # - Sell when Z-score crosses back above exit threshold
                
                # Get thresholds from parameters
                entry_z = self.params['entry_z_score']
                exit_z = self.params['exit_z_score']
                
                # Check if we have an open position
                if self.current_position is None:
                    # Entry signal - price is significantly below mean (oversold)
                    if current['z_score'] < -entry_z:
                        return 'BUY'
                else:
                    # Exit signal - price has returned to or above the mean
                    if current['z_score'] >= exit_z:
                        return 'SELL'
            
            return 'HOLD'
            
        except KeyError as e: # Handles missing keys in DataFrame
            self.logger.error(f"KeyError generating trading signal: Missing key {str(e)}")
            self.logger.error(traceback.format_exc())
            return 'HOLD'
        except IndexError as e: # Handles out-of-bounds access in DataFrame
            self.logger.error(f"IndexError generating trading signal: {str(e)}")
            self.logger.error(traceback.format_exc())
            return 'HOLD'
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError generating trading signal: {str(e)}")
            self.logger.error(traceback.format_exc())
            return 'HOLD'
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError generating trading signal: {str(e)}")
            self.logger.error(traceback.format_exc())
            return 'HOLD'
        except Exception as e:
            self.logger.error(f"Error generating trading signal: {str(e)}")
            self.logger.error(traceback.format_exc())
            return 'HOLD'
    
    def on_candle(self, candle, balance):
        """
        Process a new candle and determine trading actions
        
        Parameters
        ----------
        candle : pandas.Series
            A single candle with OHLCV data
        balance : float
            Current account balance
            
        Returns
        -------
        dict or None
            Trading action to take, or None if no action
        """
        try:
            # Convert Series to DataFrame for indicator calculation if needed
            df = pd.DataFrame([candle])
            df = self.calculate_indicators(df)
            
            # Safely access the updated candle
            try:
                candle = df.iloc[0]
            except IndexError:
                self.logger.error("Failed to process candle data")
                return None
            
            # Generate signal
            signal = self.generate_signal(df)
            
            # Get current price safely
            if 'close' not in candle:
                self.logger.error("Missing 'close' price in candle")
                return None
                
            current_price = candle['close']
            
            # Execute trading logic
            if signal == 'BUY' and self.current_position is None:
                # Calculate position size (95% of balance by default)
                size_pct = self.params['position_size_pct'] / 100.0
                size = (balance * size_pct) / current_price
                
                if size <= 0:
                    self.logger.warning(f"Calculated invalid position size: {size}")
                    return None
                
                # Calculate stop loss and take profit
                stop_loss, take_profit = self.calculate_exit_points(current_price, 'BUY')
                
                # Return action
                return {
                    'action': 'BUY',
                    'price': current_price,
                    'size': size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
            elif signal == 'SELL' and self.current_position is not None:
                return {
                    'action': 'SELL',
                    'price': current_price,
                    'size': self.current_position.size
                }
            
            return None
            
        except KeyError as e: # Handles missing keys in candle or self.params
            self.logger.error(f"KeyError processing candle: Missing key {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        except IndexError as e: # Handles out-of-bounds access in DataFrame
            self.logger.error(f"IndexError processing candle: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError processing candle: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError processing candle: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        except Exception as e:
            self.logger.error(f"Error processing candle: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        
    def calculate_exit_points(self, entry_price, side='BUY'):
        """
        Calculate stop loss and take profit levels
        
        Parameters
        ----------
        entry_price : float
            The entry price of the position
        side : str
            Trading direction - 'BUY' for long, 'SELL' for short
            
        Returns
        -------
        tuple
            (stop_loss_price, take_profit_price)
        """
        try:
            # Get percentages from parameters and convert to decimal
            stop_loss_pct = self.params['stop_loss_percentage'] / 100.0
            take_profit_pct = self.params['take_profit_percentage'] / 100.0
            
            # Ensure entry price is valid
            if not entry_price or entry_price <= 0:
                self.logger.error(f"Invalid entry price for exit calculation: {entry_price}")
                # Return fallback values
                return (0, float('inf')) if side == 'BUY' else (float('inf'), 0)
            
            # Calculate levels based on position side
            if side == 'BUY':
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
            else:  # SELL (short)
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)
            
            return stop_loss, take_profit
            
        except KeyError as e: # Handles missing keys in self.params
            self.logger.error(f"KeyError calculating exit points: Missing key {str(e)}")
            # Return fallback values
            return (entry_price * 0.95, entry_price * 1.05) if side == 'BUY' else (entry_price * 1.05, entry_price * 0.95)
        except TypeError as e: # Handles type mismatches in operations (e.g., non-numeric entry_price)
            self.logger.error(f"TypeError calculating exit points: {str(e)}")
            # Return fallback values
            return (entry_price * 0.95, entry_price * 1.05) if side == 'BUY' else (entry_price * 1.05, entry_price * 0.95)
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError calculating exit points: {str(e)}")
            # Return fallback values
            return (entry_price * 0.95, entry_price * 1.05) if side == 'BUY' else (entry_price * 1.05, entry_price * 0.95)
        except Exception as e:
            self.logger.error(f"Error calculating exit points: {str(e)}")
            # Return fallback values
            return (entry_price * 0.95, entry_price * 1.05) if side == 'BUY' else (entry_price * 1.05, entry_price * 0.95)
