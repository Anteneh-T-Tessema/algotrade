#!/usr/bin/env python3
"""
Trend Following Strategy

This strategy identifies and trades in the direction of established trends using
moving average crossovers and other trend indicators. It combines multiple
technical analysis methods:

1. Moving Average Crossovers - Fast EMA crossing over Slow EMA for trend direction
2. MACD (Moving Average Convergence Divergence) - For trend confirmation
3. ATR (Average True Range) - For volatility-based stop losses
4. ADX (Average Directional Index) - For measuring trend strength (optional)

The strategy goes long when fast EMA crosses above slow EMA with confirmation
from MACD and ADX (if enabled). It exits positions when the trend reverses.
"""

from strategies.base_strategy import Strategy, PositionSide
import pandas as pd
import numpy as np
import logging
import traceback


class TrendFollowingStrategy(Strategy):
    """
    Trend Following Strategy using moving average crossovers and momentum
    """
    
    def __init__(self, name="TrendFollowing", params=None):
        """Initialize the strategy with parameters"""
        default_params = {
            'fast_ma_period': 9,       # Fast moving average period
            'slow_ma_period': 21,      # Slow moving average period
            'signal_ma_period': 9,     # MACD signal line period
            'atr_period': 14,          # Average True Range period for volatility
            'stop_loss_atr_mult': 2.0, # Stop loss as multiple of ATR
            'trend_threshold': 0.02,   # Minimum trend strength (0.02 = 2%)
            'use_macd': True,          # Use MACD for trend confirmation 
            'use_adx': False,          # Use ADX for trend strength
            'adx_threshold': 25,       # Minimum ADX value to consider a strong trend
            'position_size_pct': 95.0  # Position size as percentage of available capital
        }
        
        # Override default params with any provided ones
        self.params = {**default_params, **(params or {})}
        
        super().__init__(name, self.params)
        self.logger = logging.getLogger(f"strategy.{name}")
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for trend following
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with added technical indicators
            
        Notes:
        ------
        Adds the following columns to the DataFrame:
        - fast_ema: Fast Exponential Moving Average
        - slow_ema: Slow Exponential Moving Average
        - macd_line, macd_signal, macd_hist: MACD indicators (if enabled)
        - atr: Average True Range for volatility measurement
        - adx, +di, -di: Directional Movement indicators (if enabled)
        - trend: Numeric trend direction (1 for up, -1 for down)
        """
        # Check if dataframe is empty or invalid
        if df is None or df.empty:
            self.logger.warning("Empty dataframe provided to calculate_indicators")
            return df
            
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return df  # Return original df without calculations
        
        try:
            # Make a copy to avoid modifying the original
            result = df.copy()
            
            # Calculate moving averages - ensure valid periods
            fast_period = int(max(1, self.params['fast_ma_period']))
            slow_period = int(max(1, self.params['slow_ma_period']))
            
            # Calculate exponential moving averages
            result['fast_ema'] = result['close'].ewm(span=fast_period, adjust=False).mean()
            result['slow_ema'] = result['close'].ewm(span=slow_period, adjust=False).mean()
            
            # Calculate MACD if enabled
            if self.params['use_macd']:
                # MACD Line = Fast EMA - Slow EMA
                result['macd_line'] = result['fast_ema'] - result['slow_ema']
                
                # MACD Signal Line = EMA of MACD Line
                signal_period = int(max(1, self.params['signal_ma_period']))
                result['macd_signal'] = result['macd_line'].ewm(span=signal_period, adjust=False).mean()
                
                # MACD Histogram = MACD Line - MACD Signal Line
                result['macd_hist'] = result['macd_line'] - result['macd_signal']
            
            # Calculate Average True Range for volatility-based stops
            atr_period = int(max(1, self.params['atr_period']))
            
            # True Range calculation
            result['tr1'] = abs(result['high'] - result['low'])
            result['tr2'] = abs(result['high'] - result['close'].shift())
            result['tr3'] = abs(result['low'] - result['close'].shift())
            result['true_range'] = result[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Average True Range
            result['atr'] = result['true_range'].rolling(window=atr_period).mean()
            
            # Clean up temporary columns
            result = result.drop(['tr1', 'tr2', 'tr3'], axis=1)
            
            # Calculate ADX if enabled (Average Directional Index)
            if self.params['use_adx']:
                # Directional Movement
                result['+dm'] = np.where((result['high'] > result['high'].shift()) & 
                                        (result['high'] - result['high'].shift() > result['low'].shift() - result['low']),
                                        result['high'] - result['high'].shift(), 0)
                result['-dm'] = np.where((result['low'].shift() > result['low']) & 
                                        (result['low'].shift() - result['low'] > result['high'] - result['high'].shift()),
                                        result['low'].shift() - result['low'], 0)
                
                # Directional Index calculation - avoid division by zero
                result['+di'] = 100 * result['+dm'].ewm(span=atr_period, adjust=False).mean() / (result['atr'] + 1e-10)
                result['-di'] = 100 * result['-dm'].ewm(span=atr_period, adjust=False).mean() / (result['atr'] + 1e-10)
                
                result['di_diff'] = abs(result['+di'] - result['-di'])
                result['di_sum'] = result['+di'] + result['-di'] + 1e-10  # Avoid division by zero
                result['dx'] = 100 * result['di_diff'] / result['di_sum']
                
                # Average Directional Index
                result['adx'] = result['dx'].ewm(span=atr_period, adjust=False).mean()
                
                # Clean up temporary columns
                result = result.drop(['+dm', '-dm', 'di_diff', 'di_sum', 'dx'], axis=1)
            
            # Add trend direction indicator
            result['trend'] = np.where(result['fast_ema'] > result['slow_ema'], 1, -1)
            
            return result
            
        except KeyError as e: # Handles missing keys in self.params or df
            self.logger.error(f"KeyError in calculate_indicators: Missing key {str(e)}")
            self.logger.debug(traceback.format_exc())
            return df
        except ValueError as e: # Handles issues with data values (e.g. during conversions, ewm mean calculation)
            self.logger.error(f"ValueError in calculate_indicators: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return df
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError in calculate_indicators: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return df
        except AttributeError as e: # Handles issues with method calls on incorrect types
            self.logger.error(f"AttributeError in calculate_indicators: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return df
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return df  # Return original df on error
    
    def generate_signal(self, df):
        """
        Generate trading signals based on trend indicators
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data and indicators
            
        Returns:
        --------
        str
            'BUY': Enter a long position
            'SELL': Exit a position or enter a short position
            'HOLD': No action
            
        Notes:
        ------
        The strategy looks for:
        1. Crossovers of fast and slow EMAs
        2. Trend strength based on price momentum
        3. MACD confirmation (if enabled)
        4. ADX confirmation for trend strength (if enabled)
        """
        try:
            # Check if we have enough data
            min_required = max(self.params['slow_ma_period'], self.params['atr_period']) + 5
            if df is None or df.empty or len(df) < min_required:
                self.logger.debug(f"Not enough data for signal generation, needed {min_required} candles")
                return 'HOLD'
            
            # Get the last two candles for crossover detection
            if len(df) < 2:
                self.logger.warning("Need at least 2 candles to detect crossovers")
                return 'HOLD'
                
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Check if we have all required indicators
            required_columns = ['fast_ema', 'slow_ema', 'atr', 'trend']
            if self.params['use_macd']:
                required_columns.extend(['macd_line', 'macd_signal', 'macd_hist'])
            if self.params['use_adx']:
                required_columns.append('adx')
                
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.debug(f"Missing indicators: {missing_columns}, recalculating")
                df = self.calculate_indicators(df)
                
                # Check if recalculation succeeded
                still_missing = [col for col in required_columns if col not in df.columns]
                if still_missing:
                    self.logger.error(f"Failed to calculate indicators: {still_missing}")
                    return 'HOLD'
                    
                current = df.iloc[-1]
                previous = df.iloc[-2]
            
            # Don't trade until we have enough data for indicators
            if pd.isna(current['fast_ema']) or pd.isna(current['slow_ema']) or pd.isna(current['atr']):
                self.logger.debug("NaN values in indicator data")
                return 'HOLD'
            
            # Detect crossovers - crossing from below to above means bullish
            fast_cross_above = previous['fast_ema'] <= previous['slow_ema'] and current['fast_ema'] > current['slow_ema']
            fast_cross_below = previous['fast_ema'] >= previous['slow_ema'] and current['fast_ema'] < current['slow_ema']
            
            # Check the trend strength using price momentum
            shift_period = min(self.params['slow_ma_period'], len(df)-1)  # Ensure we don't shift beyond data length
            close_shifted = df['close'].shift(shift_period)
            if pd.isna(close_shifted.iloc[-1]):
                trend_strength = 0  # Not enough data to calculate
            else:
                trend_strength = abs(current['close'] - close_shifted.iloc[-1]) / (close_shifted.iloc[-1] + 1e-10)
            
            strong_trend = trend_strength > self.params['trend_threshold']
            
            # MACD confirmation
            macd_bullish = False
            macd_bearish = False
            if self.params['use_macd']:
                # Bullish when MACD line crosses above signal line
                macd_bullish = previous['macd_line'] <= previous['macd_signal'] and current['macd_line'] > current['macd_signal']
                # Bearish when MACD line crosses below signal line
                macd_bearish = previous['macd_line'] >= previous['macd_signal'] and current['macd_line'] < current['macd_signal']
            
            # ADX confirmation for trend strength
            strong_adx = True  # Default if not using ADX
            if self.params['use_adx']:
                strong_adx = current['adx'] > self.params['adx_threshold']
            
            # Check if we have an open position
            if self.current_position is None:
                # Entry signal for long positions
                if fast_cross_above and strong_trend and (not self.params['use_macd'] or macd_bullish) and strong_adx:
                    self.logger.info(f"BUY signal generated: cross={fast_cross_above}, trend={trend_strength:.4f}, macd={macd_bullish}, adx={strong_adx}")
                    return 'BUY'
            else:
                # Exit signal for long positions
                if fast_cross_below or (self.params['use_macd'] and macd_bearish):
                    self.logger.info(f"SELL signal generated: cross={fast_cross_below}, macd={macd_bearish}")
                    return 'SELL'
            
            return 'HOLD'
            
        except KeyError as e: # Handles missing keys in DataFrame or self.params
            self.logger.error(f"KeyError in generate_signal: Missing key {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except IndexError as e: # Handles out-of-bounds access in DataFrame
            self.logger.error(f"IndexError in generate_signal: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except AttributeError as e: # Handles missing attributes
            self.logger.error(f"AttributeError in generate_signal: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError in generate_signal: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError in generate_signal: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except Exception as e:
            self.logger.error(f"Error generating signal: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return 'HOLD'  # Safe default on error
    
    def on_candle(self, candle, balance):
        """
        Process a new candle and determine trading actions
        
        Parameters:
        -----------
        candle : pandas.Series
            Current price candle with OHLCV data
        balance : float
            Current account balance available for trading
            
        Returns:
        --------
        dict or None
            Trading action dictionary if a trade should be made, None otherwise
            Format: {'action': 'BUY'/'SELL', 'price': float, 'size': float, ...}
        """
        try:
            # Ensure we have a valid candle
            if candle is None or not isinstance(candle, (pd.Series, dict)):
                self.logger.error(f"Invalid candle format: {type(candle)}")
                return None
                
            # Convert dict to Series if necessary
            if isinstance(candle, dict):
                candle = pd.Series(candle)
                
            # Check for required price fields
            required_fields = ['open', 'high', 'low', 'close']
            if not all(field in candle.index for field in required_fields):
                self.logger.error(f"Missing required price fields in candle")
                return None
                
            # Ensure we have numeric price data    
            if not all(isinstance(candle[field], (int, float)) for field in required_fields):
                self.logger.error(f"Non-numeric price data in candle")
                return None
            
            # Convert Series to DataFrame for indicator calculation if needed
            df = pd.DataFrame([candle]).T
            df = self.calculate_indicators(df)
            
            # Ensure indicators were calculated successfully
            if 'fast_ema' not in df.columns or 'slow_ema' not in df.columns:
                self.logger.warning("Failed to calculate indicators")
                return None
                
            # Get updated candle with indicators  
            candle = df.iloc[:,0]
            
            # Generate signal
            signal = self.generate_signal(df)
            
            # Get current price
            current_price = candle['close']
            
            # Validate price
            if current_price <= 0:
                self.logger.warning(f"Invalid price: {current_price}")
                return None
                
            # Validate balance
            if balance <= 0:
                self.logger.warning(f"Insufficient balance: {balance}")
                return None
            
            # Execute trading logic based on signal
            if signal == 'BUY' and self.current_position is None:
                # Calculate position size
                size_pct = min(max(0, self.params['position_size_pct']), 100) / 100.0  # Ensure valid percentage
                size = (balance * size_pct) / current_price
                
                # Ensure minimum viable position size
                if size * current_price < 10:  # Example minimum of $10
                    self.logger.info(f"Position too small: {size * current_price:.2f} < $10")
                    return None
                
                # Calculate stop loss and take profit
                stop_loss, take_profit = self.calculate_exit_points(current_price, 'BUY', 
                                                                   candle['atr'] if 'atr' in candle else None)
                
                # Return action
                return {
                    'action': 'BUY',
                    'price': current_price,
                    'size': size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'reason': 'trend_following_signal'
                }
            elif signal == 'SELL' and self.current_position is not None:
                return {
                    'action': 'SELL',
                    'price': current_price,
                    'size': self.current_position.size,
                    'reason': 'trend_reversal'
                }
            
            return None
            
        except KeyError as e: # Handles missing keys in candle or self.params
            self.logger.error(f"KeyError in on_candle: Missing key {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error(f"TypeError in on_candle: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError in on_candle: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
        except AttributeError as e: # Handles missing attributes
            self.logger.error(f"AttributeError in on_candle: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
        except Exception as e:
            self.logger.error(f"Error in on_candle: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return None
    
    def calculate_exit_points(self, entry_price, side='BUY', atr=None):
        """
        Calculate stop loss and take profit levels based on ATR or percentage
        
        Parameters:
        -----------
        entry_price : float
            Entry price for the position
        side : str
            Position side ('BUY' for long, 'SELL' for short)
        atr : float, optional
            Average True Range value for volatility-based exits
            
        Returns:
        --------
        tuple
            (stop_loss_price, take_profit_price)
            
        Notes:
        ------
        Uses ATR-based exits if ATR is provided, otherwise falls back to percentage-based.
        For long positions:
            - Stop loss is set below entry price
            - Take profit is set above entry price
        For short positions:
            - Stop loss is set above entry price
            - Take profit is set below entry price
        """
        try:
            # Validate entry price
            if entry_price is None or entry_price <= 0:
                self.logger.error(f"Invalid entry price: {entry_price}")
                return None, None
                
            # Use ATR for stop loss if available and valid
            if atr is not None and not pd.isna(atr) and atr > 0:
                # Get ATR multiplier with safety bounds
                atr_multiplier = max(0.5, min(10.0, self.params['stop_loss_atr_mult']))
                
                # Calculate R:R ratio (default 2:1)
                risk_reward_ratio = 2.0
                
                if side == 'BUY':
                    stop_loss = entry_price - (atr * atr_multiplier)
                    take_profit = entry_price + (atr * atr_multiplier * risk_reward_ratio)
                else:  # SELL (short)
                    stop_loss = entry_price + (atr * atr_multiplier)
                    take_profit = entry_price - (atr * atr_multiplier * risk_reward_ratio)
                    
                # Log calculated levels
                self.logger.debug(f"ATR-based exits - SL: {stop_loss:.2f}, TP: {take_profit:.2f} (ATR: {atr:.4f})")
                    
            else:
                # Fall back to percentage-based if ATR is not available
                # Get percentages with safety bounds
                stop_loss_pct = max(0.005, min(0.1, self.params.get('stop_loss_percentage', 2.0) / 100))
                take_profit_pct = max(0.005, min(0.2, self.params.get('take_profit_percentage', 4.0) / 100))
                
                if side == 'BUY':
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                else:  # SELL (short)
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - take_profit_pct)
                
                # Log calculated levels
                self.logger.debug(f"Percentage-based exits - SL: {stop_loss:.2f} ({stop_loss_pct*100:.1f}%), " 
                                 f"TP: {take_profit:.2f} ({take_profit_pct*100:.1f}%)")
                
            # Ensure stop loss is not too close to entry (minimum 0.1%)
            if side == 'BUY' and stop_loss > entry_price * 0.999:
                stop_loss = entry_price * 0.999
                self.logger.warning(f"Stop loss too close to entry, adjusted to {stop_loss:.2f}")
            elif side == 'SELL' and stop_loss < entry_price * 1.001:
                stop_loss = entry_price * 1.001
                self.logger.warning(f"Stop loss too close to entry, adjusted to {stop_loss:.2f}")
                
            return stop_loss, take_profit
            
        except TypeError as e: # Handles type mismatches in operations (e.g., non-numeric entry_price)
            self.logger.error(f"TypeError in calculate_exit_points: {str(e)}")
            self.logger.debug(traceback.format_exc())
            # Return default values as fallback
            default_sl = entry_price * 0.98 if side == 'BUY' else entry_price * 1.02
            default_tp = entry_price * 1.04 if side == 'BUY' else entry_price * 0.96
            return default_sl, default_tp
        except ValueError as e: # Handles issues with data values
            self.logger.error(f"ValueError in calculate_exit_points: {str(e)}")
            self.logger.debug(traceback.format_exc())
            # Return default values as fallback
            default_sl = entry_price * 0.98 if side == 'BUY' else entry_price * 1.02
            default_tp = entry_price * 1.04 if side == 'BUY' else entry_price * 0.96
            return default_sl, default_tp
        except KeyError as e: # Handles missing keys in self.params
            self.logger.error(f"KeyError in calculate_exit_points: Missing key {str(e)}")
            self.logger.debug(traceback.format_exc())
            # Return default values as fallback
            default_sl = entry_price * 0.98 if side == 'BUY' else entry_price * 1.02
            default_tp = entry_price * 1.04 if side == 'BUY' else entry_price * 0.96
            return default_sl, default_tp
        except Exception as e:
            self.logger.error(f"Error calculating exit points: {str(e)}")
            # Return default values as fallback
            default_sl = entry_price * 0.98 if side == 'BUY' else entry_price * 1.02
            default_tp = entry_price * 1.04 if side == 'BUY' else entry_price * 0.96
            return default_sl, default_tp
