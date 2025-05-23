#!/usr/bin/env python3
"""
Grid Trading Strategy

This strategy places a grid of buy and sell orders at fixed price intervals.
It profits from price movements in either direction within a range.
"""

from strategies.base_strategy import Strategy, PositionSide, Position
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional


class GridPosition(Position):
    """Extended Position class for grid trading with grid level"""
    def __init__(self, symbol, entry_price, size, side=PositionSide.LONG, grid_level=0):
        super().__init__(symbol, entry_price, size, side)
        self.grid_level = grid_level


class GridTradingStrategy(Strategy):
    """
    Grid Trading Strategy that places orders at specified price intervals
    """
    
    def __init__(self, name="GridTrading", params=None):
        """
        Initialize the strategy with parameters

        Parameters:
        -----------
        name : str
            Strategy name
        params : dict, optional
            Strategy parameters including:
            - grid_levels: Number of grid levels (both buy and sell)
            - grid_size_pct: Grid size as percentage of price (1.0 = 1%)
            - total_investment: Total investment amount
            - upper_limit_pct: Upper price limit as percentage above reference price
            - lower_limit_pct: Lower price limit as percentage below reference price
            - reference_price_type: 'current', 'ma', or 'auto'
            - reference_ma_period: Moving average period for reference price
            - dynamic_grid: Whether to adjust the grid dynamically
            - rebalance_frequency: How often to rebalance the grid (in hours)
            - partial_fill: Whether to allow partial fills of grid levels
            - position_size_pct: Each grid level uses this percentage of total capital
        """
        default_params = {
            'grid_levels': 10,          # Number of grid levels (both buy and sell)
            'grid_size_pct': 1.0,       # Grid size as percentage of price (1.0 = 1%)
            'total_investment': 1000,    # Total investment amount
            'upper_limit_pct': 10.0,     # Upper price limit as percentage above reference price
            'lower_limit_pct': 10.0,     # Lower price limit as percentage below reference price
            'reference_price_type': 'current',  # 'current', 'ma', 'auto'
            'reference_ma_period': 20,   # Moving average period for reference price
            'dynamic_grid': False,       # Whether to adjust the grid dynamically
            'rebalance_frequency': 24,   # How often to rebalance the grid (in hours)
            'partial_fill': True,        # Whether to allow partial fills of grid levels
            'position_size_pct': 10.0    # Each grid level uses this percentage of total capital
        }
        
        # Override default params with any provided ones
        self.params = {**default_params, **(params or {})}
        
        # Validate parameters
        try:
            self._validate_parameters()
        except ValueError as e:
            self.logger = logging.getLogger(f"strategy.{name}")
            self.logger.error(f"Parameter validation error: {str(e)}")
            raise
        
        super().__init__(name, self.params)
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Grid-specific attributes
        self.grid_levels = []           # List of price levels for the grid
        self.grid_positions = []        # List of active positions in the grid
        self.last_rebalance_time = None  # When the grid was last rebalanced
        self.reference_price = None      # Reference price for grid calculation
        self.candles_processed = 0       # Counter for processed candles
        
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
            'grid_levels', 'grid_size_pct', 'total_investment', 
            'upper_limit_pct', 'lower_limit_pct', 'reference_ma_period',
            'rebalance_frequency', 'position_size_pct'
        ]
        
        for param in positive_params:
            if self.params[param] <= 0:
                raise ValueError(f"Parameter '{param}' must be positive. Got: {self.params[param]}")
        
        # Validate grid levels is an integer
        if not isinstance(self.params['grid_levels'], int):
            raise ValueError(f"Grid levels must be an integer. Got: {self.params['grid_levels']}")
            
        # Validate reference_price_type is valid
        valid_price_types = ['current', 'ma', 'auto']
        if self.params['reference_price_type'] not in valid_price_types:
            raise ValueError(
                f"Reference price type must be one of {valid_price_types}. "
                f"Got: {self.params['reference_price_type']}"
            )
            
        # Validate boolean parameters
        bool_params = ['dynamic_grid', 'partial_fill']
        for param in bool_params:
            if not isinstance(self.params[param], bool):
                raise ValueError(f"Parameter '{param}' must be a boolean. Got: {self.params[param]}")
                
        # Validate position size percentage is not too high
        if self.params['position_size_pct'] > 100:
            raise ValueError(
                f"Position size percentage cannot exceed 100%. "
                f"Got: {self.params['position_size_pct']}%"
            )
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators for grid trading
        
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
            
            # Calculate moving average for reference price
            ma_period = self.params['reference_ma_period']
            
            # Handle case where we don't have enough data for the moving average
            if len(result) < ma_period:
                self.logger.warning(
                    f"Not enough data for MA calculation. Need {ma_period} periods, got {len(result)}"
                )
                # Still calculate MA but it will have NaN values
                
            result['reference_ma'] = result['close'].rolling(window=ma_period).mean()
            
            # Calculate volatility (standard deviation) with safeguards
            result['volatility'] = result['close'].rolling(window=ma_period).std()
            # Avoid division by zero
            result['volatility'] = result['volatility'].div(result['close']).fillna(0)
            # Set minimum volatility to prevent extreme values
            result['volatility'] = result['volatility'].apply(lambda x: max(0.001, x))
            
            # Price range based on volatility
            result['upper_band'] = result['reference_ma'] * (1 + result['volatility'] * 2)
            result['lower_band'] = result['reference_ma'] * (1 - result['volatility'] * 2)
            
            return result
            
        except ValueError as e:
            self.logger.error(f"ValueError calculating indicators: {str(e)}")
            raise
        except KeyError as e:
            self.logger.error(f"KeyError calculating indicators: Missing key {str(e)}")
            raise
        except TypeError as e:
            self.logger.error(f"TypeError calculating indicators: {str(e)}")
            raise
        except AttributeError as e:
            self.logger.error(f"AttributeError calculating indicators: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def setup_grid(self, reference_price):
        """
        Set up the grid levels based on reference price
        
        Parameters:
        -----------
        reference_price : float
            Reference price for grid calculation
            
        Returns:
        --------
        list
            List of price levels for the grid
            
        Raises:
        -------
        ValueError
            If reference price is invalid or grid cannot be calculated
        """
        try:
            # Validate reference price
            if reference_price is None or reference_price <= 0:
                raise ValueError(f"Invalid reference price: {reference_price}")
                
            self.reference_price = reference_price
            
            # Calculate upper and lower limits
            upper_limit = reference_price * (1 + self.params['upper_limit_pct'] / 100)
            lower_limit = reference_price * (1 - self.params['lower_limit_pct'] / 100)
            
            # Ensure lower limit is greater than zero
            lower_limit = max(0.00001, lower_limit)
            
            # Calculate grid interval
            grid_levels = self.params['grid_levels']
            price_range = upper_limit - lower_limit
            
            # Check if price range is valid
            if price_range <= 0:
                raise ValueError(f"Invalid price range: {price_range}. Upper limit: {upper_limit}, Lower limit: {lower_limit}")
                
            grid_interval = price_range / grid_levels
            
            # Validate grid interval
            if grid_interval <= 0:
                raise ValueError(f"Invalid grid interval: {grid_interval}")
                
            # Generate grid levels
            self.grid_levels = []
            for i in range(grid_levels + 1):
                level = lower_limit + i * grid_interval
                self.grid_levels.append(level)
                
            # Log grid setup
            self.logger.info(f"Grid set up with {len(self.grid_levels)} levels from {lower_limit:.2f} to {upper_limit:.2f}")
            self.logger.info(f"Grid interval: {grid_interval:.2f}")
            
            return self.grid_levels
            
        except ValueError as e:
            self.logger.error(f"ValueError setting up grid: {str(e)}")
            # Return empty grid to avoid further errors
            self.grid_levels = []
            raise
        except TypeError as e:
            self.logger.error(f"TypeError setting up grid: {str(e)}")
            # Return empty grid to avoid further errors
            self.grid_levels = []
            raise
        except ArithmeticError as e:
            self.logger.error(f"ArithmeticError setting up grid: {str(e)}")
            # Return empty grid to avoid further errors
            self.grid_levels = []
            raise
        except Exception as e:
            self.logger.error(f"Error setting up grid: {str(e)}")
            # Return empty grid to avoid further errors
            self.grid_levels = []
            raise
    
    def generate_signal(self, df):
        """
        Generate trading signals based on grid levels
        
        For grid trading, this doesn't follow the usual BUY/SELL/HOLD pattern
        as grid trading requires more complex logic for multiple positions.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data and indicators
            
        Returns:
        --------
        str
            'BUY', 'SELL', or 'HOLD' signal
            
        Raises:
        -------
        ValueError
            If input data is invalid
        """
        try:
            # Check if dataframe is empty or too small
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to generate_signal")
                return 'HOLD'
                
            # Validate dataframe has required columns
            if 'close' not in df.columns:
                raise ValueError("DataFrame is missing 'close' column")
                
            # Check if we have enough data for MA calculation
            if len(df) < self.params['reference_ma_period']:
                self.logger.warning(
                    f"Not enough data for signal generation. Need {self.params['reference_ma_period']} periods, got {len(df)}"
                )
                return 'HOLD'
            
            # Get the latest candle
            current = df.iloc[-1]
            current_price = current['close']
            
            # Validate price is positive
            if current_price <= 0:
                self.logger.warning(f"Invalid price detected: {current_price}")
                return 'HOLD'
            
            # Set up grid if not done yet
            if not self.grid_levels:
                try:
                    reference_price = self._get_reference_price(df)
                    self.setup_grid(reference_price)
                except ValueError as e:
                    self.logger.error(f"ValueError setting up initial grid: {str(e)}")
                    return 'HOLD'
                except KeyError as e:
                    self.logger.error(f"KeyError setting up initial grid: {str(e)}")
                    return 'HOLD'
                except TypeError as e:
                    self.logger.error(f"TypeError setting up initial grid: {str(e)}")
                    return 'HOLD'
            
            # Check if we need to rebalance the grid
            try:
                if self._should_rebalance(df):
                    reference_price = self._get_reference_price(df)
                    self.setup_grid(reference_price)
                    self.last_rebalance_time = df.index[-1]
                    self.logger.info(f"Grid rebalanced at {df.index[-1]} with reference price {reference_price:.2f}")
            except ValueError as e:
                self.logger.error(f"ValueError during grid rebalancing: {str(e)}")
            except KeyError as e:
                self.logger.error(f"KeyError during grid rebalancing: {str(e)}")
            except TypeError as e:
                self.logger.error(f"TypeError during grid rebalancing: {str(e)}")
            except IndexError as e:
                self.logger.error(f"IndexError during grid rebalancing: {str(e)}")
            
            # In a real grid trading system, we would set up all levels at once
            # But for backtesting purposes, we'll check if the price crosses grid levels
            
            # We just return HOLD here as the on_candle method will handle the grid signals
            return 'HOLD'
            
        except ValueError as e:
            self.logger.error(f"ValueError generating signal: {str(e)}")
            return 'HOLD'  # Default to HOLD on error
        except KeyError as e:
            self.logger.error(f"KeyError generating signal: Missing key {str(e)}")
            return 'HOLD'  # Default to HOLD on error
        except IndexError as e:
            self.logger.error(f"IndexError generating signal: {str(e)}")
            return 'HOLD'  # Default to HOLD on error
        except Exception as e:
            self.logger.error(f"Error generating signal: {str(e)}")
            return 'HOLD'  # Default to HOLD on error
    
    def on_candle(self, candle, balance):
        """
        Process a new candle and determine grid trading actions
        
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
            If input data is invalid or processing fails
        """
        try:
            # Validate inputs
            if candle is None:
                raise ValueError("Candle data is None")
                
            if balance <= 0:
                self.logger.warning(f"Invalid balance: {balance}. Must be positive.")
                return None
                
            # Check required fields in candle
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in candle:
                    raise ValueError(f"Candle data missing required field: {field}")
            
            # Increment counter
            self.candles_processed += 1
            
            # Convert to DataFrame for indicator calculations
            try:
                df = pd.DataFrame([candle])
                df = self.calculate_indicators(df)
                
                if df is None or df.empty:
                    raise ValueError("Failed to calculate indicators")
                    
                candle = df.iloc[0]
            except ValueError as e:
                self.logger.error(f"ValueError calculating indicators in on_candle: {str(e)}")
                return None
            except KeyError as e:
                self.logger.error(f"KeyError calculating indicators in on_candle: {str(e)}")
                return None
            except TypeError as e:
                self.logger.error(f"TypeError calculating indicators in on_candle: {str(e)}")
                return None
            except IndexError as e:
                self.logger.error(f"IndexError calculating indicators in on_candle: {str(e)}")
                return None
            
            # Current price
            current_price = candle['close']
            
            # Validate price
            if current_price <= 0:
                self.logger.warning(f"Invalid price: {current_price}")
                return None
            
            # Initialize grid if needed
            if not self.grid_levels:
                try:
                    reference_price = self._get_reference_price(df)
                    self.setup_grid(reference_price)
                    self.last_rebalance_time = pd.to_datetime(candle.name)
                except ValueError as e:
                    self.logger.error(f"ValueError initializing grid: {str(e)}")
                    return None
                except KeyError as e:
                    self.logger.error(f"KeyError initializing grid: {str(e)}")
                    return None
                except TypeError as e:
                    self.logger.error(f"TypeError initializing grid: {str(e)}")
                    return None
                except AttributeError as e:
                    self.logger.error(f"AttributeError initializing grid: {str(e)}")
                    return None
            
            # Get the grid level that this price falls between
            try:
                current_level = self._get_current_level(current_price)
                if current_level is None:
                    self.logger.warning(f"Could not determine grid level for price {current_price}")
            except ValueError as e:
                self.logger.error(f"ValueError getting current grid level: {str(e)}")
                return None
            except TypeError as e:
                self.logger.error(f"TypeError getting current grid level: {str(e)}")
                return None
            except IndexError as e:
                self.logger.error(f"IndexError getting current grid level: {str(e)}")
                return None
            
            # If we don't have any positions yet, initialize grid positions
            if not self.grid_positions and self.candles_processed > 5:  # Give some warmup period
                try:
                    return self._initialize_grid_positions(current_price, balance)
                except ValueError as e:
                    self.logger.error(f"ValueError initializing grid positions: {str(e)}")
                    return None
                except TypeError as e:
                    self.logger.error(f"TypeError initializing grid positions: {str(e)}")
                    return None
                except KeyError as e:
                    self.logger.error(f"KeyError initializing grid positions: {str(e)}")
                    return None
                except ZeroDivisionError as e:
                    self.logger.error(f"ZeroDivisionError initializing grid positions: {str(e)}")
                    return None
            
            # Check existing positions against grid levels for potential exits
            try:
                exit_actions = self._check_exit_signals(current_price)
                if exit_actions:
                    return exit_actions
            except ValueError as e:
                self.logger.error(f"ValueError checking exit signals: {str(e)}")
            except TypeError as e:
                self.logger.error(f"TypeError checking exit signals: {str(e)}")
            except KeyError as e:
                self.logger.error(f"KeyError checking exit signals: {str(e)}")
            except IndexError as e:
                self.logger.error(f"IndexError checking exit signals: {str(e)}")
            
            # Check for new entry opportunities
            try:
                entry_actions = self._check_entry_signals(current_price, balance)
                if entry_actions:
                    return entry_actions
            except ValueError as e:
                self.logger.error(f"ValueError checking entry signals: {str(e)}")
            except TypeError as e:
                self.logger.error(f"TypeError checking entry signals: {str(e)}")
            except KeyError as e:
                self.logger.error(f"KeyError checking entry signals: {str(e)}")
            except IndexError as e:
                self.logger.error(f"IndexError checking entry signals: {str(e)}")
            
            # No actions to take
            return None
            
        except ValueError as e:
            self.logger.error(f"ValueError processing candle: {str(e)}")
            return None
        except KeyError as e:
            self.logger.error(f"KeyError processing candle: Missing key {str(e)}")
            return None
        except TypeError as e:
            self.logger.error(f"TypeError processing candle: {str(e)}")
            return None
        except IndexError as e:
            self.logger.error(f"IndexError processing candle: {str(e)}")
            return None
        except AttributeError as e:
            self.logger.error(f"AttributeError processing candle: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing candle: {str(e)}")
            return None
    
    def _initialize_grid_positions(self, current_price, balance):
        """Initialize positions around the current price"""
        # First determine how much capital per grid level
        grid_levels = self.params['grid_levels']
        capital_per_level = balance * (self.params['position_size_pct'] / 100) / grid_levels
        
        # Find which grid level the current price is closest to
        closest_level = min(self.grid_levels, key=lambda x: abs(x - current_price))
        closest_index = self.grid_levels.index(closest_level)
        
        # Open a position at current level
        size = capital_per_level / current_price
        
        return {
            'action': 'BUY',
            'price': current_price,
            'size': size,
            'grid_level': closest_index
        }
    
    def _check_exit_signals(self, current_price):
        """Check if any positions should be exited based on grid levels"""
        if not self.grid_positions or not self.current_position:
            return None
            
        # Get the current grid level
        current_level_idx = self._get_current_level(current_price)
        if current_level_idx is None or current_level_idx >= len(self.grid_levels) - 1:
            return None
            
        # If price has moved up past a sell level, exit the position
        position = self.current_position
        entry_level = self._get_current_level(position.entry_price)
        
        # Exit if price has moved up at least one level
        if entry_level is not None and current_level_idx > entry_level:
            return {
                'action': 'SELL',
                'price': current_price,
                'size': position.size
            }
            
        return None
    
    def _check_entry_signals(self, current_price, balance):
        """Check if new positions should be entered based on grid levels"""
        # Don't enter new positions if we already have one
        if self.current_position is not None:
            return None
            
        # Get the current grid level
        current_level_idx = self._get_current_level(current_price)
        if current_level_idx is None:
            return None
            
        # Check if we're near a buy level (lower in the grid)
        if current_level_idx < len(self.grid_levels) // 2:  # In the lower half of grid
            # Calculate position size
            grid_levels = self.params['grid_levels']
            capital_per_level = balance * (self.params['position_size_pct'] / 100) / grid_levels
            size = capital_per_level / current_price
            
            return {
                'action': 'BUY',
                'price': current_price,
                'size': size,
                'grid_level': current_level_idx
            }
            
        return None
    
    def _get_current_level(self, price):
        """
        Find the grid level that the price falls between
        
        Parameters:
        -----------
        price : float
            Current price
            
        Returns:
        --------
        int or None
            Index of the grid level the price falls between, or None if grid is not set up
            
        Raises:
        -------
        ValueError
            If price is invalid
        """
        try:
            # Validate price
            if price is None:
                raise ValueError("Price is None")
                
            if not isinstance(price, (int, float)):
                raise ValueError(f"Price must be a number. Got: {type(price)}")
                
            if price <= 0:
                raise ValueError(f"Price must be positive. Got: {price}")
                
            # Check if grid is set up
            if not self.grid_levels:
                self.logger.warning("Grid levels not set up yet")
                return None
                
            # Validate grid levels
            if len(self.grid_levels) < 2:
                self.logger.warning(f"Insufficient grid levels: {len(self.grid_levels)}")
                return None
                
            # Handle price below lowest grid level
            if price < self.grid_levels[0]:
                return 0
                
            # Handle price above highest grid level
            if price > self.grid_levels[-1]:
                return len(self.grid_levels) - 1
                
            # Find which level bracket the price falls in
            for i in range(len(self.grid_levels) - 1):
                if self.grid_levels[i] <= price < self.grid_levels[i + 1]:
                    return i
                    
            # This should not happen if grid levels are set up correctly
            self.logger.warning(f"Could not find grid level for price {price}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current grid level: {str(e)}")
            return None
    
    def _get_reference_price(self, df):
        """
        Get reference price for grid calculation
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with OHLCV data and indicators
            
        Returns:
        --------
        float
            Reference price for grid calculation
            
        Raises:
        -------
        ValueError
            If reference price cannot be calculated
        """
        try:
            # Validate input
            if df is None or df.empty:
                raise ValueError("Empty dataframe provided for reference price calculation")
                
            if 'close' not in df.columns:
                raise ValueError("DataFrame is missing 'close' column")
                
            price_type = self.params['reference_price_type']
            
            # Get most recent candle
            try:
                current = df.iloc[-1]
                current_price = current['close']
                
                # Validate price
                if current_price <= 0:
                    self.logger.warning(f"Invalid current price: {current_price}. Using fallback.")
                    current_price = 1.0  # Fallback value
            except Exception as e:
                self.logger.error(f"Error getting current price: {str(e)}")
                raise ValueError("Could not get current price from dataframe")
            
            if price_type == 'current':
                # Use current price
                return current_price
                
            elif price_type == 'ma':
                # Use moving average
                try:
                    if 'reference_ma' in df.columns and not pd.isna(current['reference_ma']):
                        ma_value = current['reference_ma']
                        
                        # Validate MA value
                        if ma_value <= 0:
                            self.logger.warning(f"Invalid MA value: {ma_value}. Using current price.")
                            return current_price
                            
                        return ma_value
                    else:
                        # Calculate MA if not in dataframe
                        ma_period = self.params['reference_ma_period']
                        if len(df) >= ma_period:
                            ma_value = df['close'].iloc[-ma_period:].mean()
                            
                            # Validate calculated MA value
                            if ma_value <= 0:
                                self.logger.warning(f"Invalid calculated MA value: {ma_value}. Using current price.")
                                return current_price
                                
                            return ma_value
                        else:
                            self.logger.warning(
                                f"Not enough data for MA calculation. Need {ma_period}, got {len(df)}. Using current price."
                            )
                            return current_price
                except Exception as e:
                    self.logger.error(f"Error calculating MA reference price: {str(e)}")
                    return current_price
                    
            elif price_type == 'auto':
                # Auto-detect range based on volatility
                try:
                    if 'volatility' in df.columns and not pd.isna(current['volatility']):
                        # Use volatility-based bands
                        return current_price
                    else:
                        self.logger.warning("Volatility not available for auto reference price. Using current price.")
                        return current_price
                except Exception as e:
                    self.logger.error(f"Error calculating auto reference price: {str(e)}")
                    return current_price
                    
            else:
                self.logger.warning(f"Unknown reference price type: {price_type}. Using current price.")
                return current_price
                
        except Exception as e:
            self.logger.error(f"Error getting reference price: {str(e)}")
            # Return a default value to prevent further errors
            return 1.0  # Default fallback value
    
    def _should_rebalance(self, df):
        """Determine if the grid should be rebalanced"""
        if self.last_rebalance_time is None:
            return True
            
        if self.params['dynamic_grid']:
            current_time = df.index[-1]
            
            # Calculate hours since last rebalance
            if hasattr(current_time, 'to_pydatetime'):
                current_time = current_time.to_pydatetime()
                
            if hasattr(self.last_rebalance_time, 'to_pydatetime'):
                last_rebalance = self.last_rebalance_time.to_pydatetime()
            else:
                last_rebalance = self.last_rebalance_time
                
            hours_passed = (current_time - last_rebalance).total_seconds() / 3600
            
            return hours_passed > self.params['rebalance_frequency']
        else:
            return False
