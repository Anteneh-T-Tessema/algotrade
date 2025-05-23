#!/usr/bin/env python3
"""
Arbitrage Strategy

This strategy identifies and exploits price differences between exchanges or related assets.
It includes triangular arbitrage and cross-exchange arbitrage detection.
"""

from strategies.base_strategy import Strategy, PositionSide
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple


class ArbitrageStrategy(Strategy):
    """
    Strategy for detecting and executing arbitrage opportunities between markets
    """
    
    def __init__(self, name="Arbitrage", params=None):
        """Initialize the strategy with parameters"""
        default_params = {
            'min_profit_threshold': 0.15,  # Minimum profit threshold in percentage (0.15 = 0.15%)
            'max_position_size': 1000,    # Maximum position size in USDT
            'fee_percentage': 0.1,        # Trading fee percentage (0.1 = 0.1%)
            'slippage_percentage': 0.05,  # Expected slippage percentage (0.05 = 0.05%)
            'use_triangular': True,       # Whether to use triangular arbitrage
            'use_cross_exchange': True,   # Whether to use cross-exchange arbitrage
            'max_positions': 1,           # Maximum concurrent arbitrage positions
            'position_timeout': 5,        # Maximum time to hold position in minutes
            'position_size_pct': 95.0     # Position size as percentage of available capital
        }
        
        # Override default params with any provided ones
        self.params = {**default_params, **(params or {})}
        
        super().__init__(name, self.params)
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Track different markets for arbitrage
        self.markets = {}
        self.last_update_time = None
        
        # For triangular arbitrage
        self.exchange_rates = {}
        
        # For tracking arbitrage opportunities
        self.current_opportunity = None
        self.opportunity_time = None
    
    def update_market(self, symbol, price, timestamp=None):
        """Update market price information for a symbol"""
        self.markets[symbol] = {
            'price': price,
            'timestamp': timestamp or pd.Timestamp.now()
        }
        
        self.last_update_time = timestamp or pd.Timestamp.now()
    
    def update_exchange_rate(self, pair, rate, timestamp=None):
        """Update exchange rate for triangular arbitrage"""
        self.exchange_rates[pair] = {
            'rate': rate,
            'timestamp': timestamp or pd.Timestamp.now()
        }
    
    def calculate_indicators(self, df):
        """
        Calculate indicators for arbitrage detection
        In a real system, this would include fetching prices from different exchanges
        """
        # For simulation purposes, we'll use a simplified model
        # In a real system, you would need price data from multiple exchanges
        
        # Check if dataframe is empty
        if df is None or df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Simulate arbitrage opportunities
        result['arb_opportunity'] = False
        result['arb_profit'] = 0.0
        
        # Simulate some arbitrage opportunities based on price patterns
        if len(result) > 3:
            # Detect potential triangular arbitrage opportunities
            # In a real system, you would compare actual exchange rates
            # Here we'll just simulate some opportunities
            
            # Simulate spread volatility that might create opportunities
            spread_volatility = result['high'] - result['low']
            avg_volatility = spread_volatility.rolling(10).mean()
            
            # Simulate opportunity when volatility spikes
            volatility_ratio = spread_volatility / (avg_volatility + 1e-10)
            result['arb_opportunity'] = volatility_ratio > 1.5
            
            # Calculate simulated profit
            fee_pct = self.params['fee_percentage'] / 100
            slippage_pct = self.params['slippage_percentage'] / 100
            
            # Simulate profit based on volatility
            result.loc[result['arb_opportunity'], 'arb_profit'] = (
                volatility_ratio * 0.1 - 2 * fee_pct - slippage_pct
            )
        
        return result
    
    def detect_triangular_arbitrage(self):
        """
        Detect triangular arbitrage opportunities
        A->B->C->A should yield a profit after fees
        
        Returns:
        --------
        dict or None
            Dictionary with arbitrage details or None if no opportunity
        """
        # In a real system, this would use actual exchange rates
        # For simulation, we'll use the stored exchange rates
        
        if len(self.exchange_rates) < 3:
            return None
        
        # Triangular arbitrage requires at least 3 currency pairs forming a cycle
        # For example: BTC/USD, ETH/BTC, ETH/USD
        
        # For simulation, we'll manually check for opportunities
        # Here we assume we have these pairs: BTC/USD, ETH/BTC, ETH/USD
        btc_usd = self.exchange_rates.get('BTC/USD', {}).get('rate')
        eth_btc = self.exchange_rates.get('ETH/BTC', {}).get('rate')
        eth_usd = self.exchange_rates.get('ETH/USD', {}).get('rate')
        
        if not all([btc_usd, eth_btc, eth_usd]):
            return None
        
        # Calculate expected rate from triangular relationship
        expected_eth_usd = btc_usd * eth_btc
        
        # Calculate profit percentage after fees
        fee_pct = self.params['fee_percentage'] / 100
        slippage_pct = self.params['slippage_percentage'] / 100
        total_cost_pct = (fee_pct * 3) + slippage_pct  # 3 trades in the cycle
        
        # Calculate profit percentage
        profit_pct = (eth_usd / expected_eth_usd - 1) * 100 - total_cost_pct
        
        # Check if profit exceeds threshold
        min_profit = self.params['min_profit_threshold']
        if profit_pct > min_profit:
            return {
                'type': 'TRIANGULAR',
                'profit_pct': profit_pct,
                'path': 'USD -> BTC -> ETH -> USD',
                'rates': {
                    'BTC/USD': btc_usd,
                    'ETH/BTC': eth_btc,
                    'ETH/USD': eth_usd,
                    'expected_ETH/USD': expected_eth_usd
                }
            }
        
        return None
    
    def detect_cross_exchange_arbitrage(self):
        """
        Detect arbitrage opportunities between different exchanges
        
        Returns:
        --------
        dict or None
            Dictionary with arbitrage details or None if no opportunity
        """
        # In a real system, you would have data from multiple exchanges
        # Here we'll simulate using a synthetic price difference
        
        if len(self.markets) < 1:
            return None
        
        # Get current price
        symbol = next(iter(self.markets))
        current_price = self.markets[symbol]['price']
        
        # Simulate exchange B price with a random difference
        # In a real system, you would fetch the actual price from exchange B
        exchange_b_price = current_price * (1 + np.random.normal(0, 0.002))
        
        # Calculate profit percentage after fees and slippage
        fee_pct = self.params['fee_percentage'] / 100
        slippage_pct = self.params['slippage_percentage'] / 100
        total_cost_pct = (fee_pct * 2) + slippage_pct  # Buy on one exchange, sell on another
        
        # Calculate potential profit
        price_diff_pct = abs(exchange_b_price / current_price - 1) * 100
        profit_pct = price_diff_pct - total_cost_pct
        
        # Check if profit exceeds threshold
        min_profit = self.params['min_profit_threshold']
        if profit_pct > min_profit:
            # Determine direction
            if exchange_b_price > current_price:
                # Buy on exchange A, sell on exchange B
                direction = 'A->B'
            else:
                # Buy on exchange B, sell on exchange A
                direction = 'B->A'
                
            return {
                'type': 'CROSS_EXCHANGE',
                'profit_pct': profit_pct,
                'direction': direction,
                'prices': {
                    'exchange_A': current_price,
                    'exchange_B': exchange_b_price
                }
            }
        
        return None
    
    def generate_signal(self, df):
        """
        Generate trading signals based on arbitrage opportunities
        
        For arbitrage, this doesn't follow the usual BUY/SELL/HOLD pattern
        as arbitrage requires more complex actions on multiple markets.
        
        Returns 'ARBITRAGE' if an opportunity is detected.
        """
        # Check if we have enough data
        if df is None or df.empty:
            return 'HOLD'
            
        # Get the most recent candle
        current = df.iloc[-1]
        
        # Update market data
        self.update_market(df.name if hasattr(df, 'name') else 'UNKNOWN',
                          current['close'],
                          current.name if hasattr(current, 'name') else None)
        
        # For simulation, let's generate some exchange rates
        # In a real system, these would come from API calls to exchanges
        self.update_exchange_rate('BTC/USD', current['close'], 
                                 current.name if hasattr(current, 'name') else None)
        self.update_exchange_rate('ETH/BTC', 0.06 + np.random.normal(0, 0.001), 
                                 current.name if hasattr(current, 'name') else None)
        self.update_exchange_rate('ETH/USD', current['close'] * (0.06 + np.random.normal(0, 0.001)), 
                                 current.name if hasattr(current, 'name') else None)
        
        # Check for arbitrage opportunities
        opportunity = None
        
        if self.params['use_triangular']:
            opportunity = self.detect_triangular_arbitrage()
            
        if not opportunity and self.params['use_cross_exchange']:
            opportunity = self.detect_cross_exchange_arbitrage()
        
        if opportunity:
            self.current_opportunity = opportunity
            self.opportunity_time = pd.Timestamp.now()
            return 'ARBITRAGE'
        
        return 'HOLD'
    
    def on_candle(self, candle, balance):
        """Process a new candle and determine arbitrage actions"""
        try:
            # Convert to DataFrame for indicator calculations
            df = pd.DataFrame([candle])
            df = self.calculate_indicators(df)
            candle = df.iloc[0]
            
            # Generate signal
            signal = self.generate_signal(df)
            
            # Get current price
            current_price = candle['close']
            
            # Check for arbitrage opportunity
            if signal == 'ARBITRAGE' and self.current_position is None:
                # Calculate position size - limit to max position size
                size_pct = self.params['position_size_pct'] / 100.0
                position_size_usd = min(balance * size_pct, self.params['max_position_size'])
                size = position_size_usd / current_price
                
                # For simulation in backtesting, we'll enter a regular position
                # In a real system, this would involve executing the arbitrage across markets
                return {
                    'action': 'BUY',
                    'price': current_price,
                    'size': size,
                    'arbitrage': True,
                    'expected_profit': self.current_opportunity['profit_pct'] if self.current_opportunity else 0
                }
            
            # Exit arbitrage position after timeout or if profit target reached
            if self.current_position is not None and getattr(self.current_position, 'arbitrage', False):
                # Calculate how long we've held the position
                current_time = pd.to_datetime(candle.name) if hasattr(candle, 'name') else pd.Timestamp.now()
                position_time = self.current_position.entry_time
                
                # Convert to datetime if needed
                if hasattr(current_time, 'to_pydatetime'):
                    current_time = current_time.to_pydatetime()
                if hasattr(position_time, 'to_pydatetime'):
                    position_time = position_time.to_pydatetime()
                    
                minutes_held = (current_time - position_time).total_seconds() / 60
                
                # Exit if we've held too long
                if minutes_held >= self.params['position_timeout']:
                    return {
                        'action': 'SELL',
                        'price': current_price,
                        'size': self.current_position.size,
                        'reason': 'TIMEOUT'
                    }
                
                # Exit if we've reached our profit target
                if 'expected_profit' in self.current_position.__dict__:
                    current_profit_pct = ((current_price / self.current_position.entry_price) - 1) * 100
                    if current_profit_pct >= self.current_position.expected_profit:
                        return {
                            'action': 'SELL',
                            'price': current_price,
                            'size': self.current_position.size,
                            'reason': 'PROFIT_TARGET'
                        }
            
            return None
        except TypeError as e:
            self.logger.error(f"Type error in on_candle: {str(e)}")
            return None
        except AttributeError as e:
            self.logger.error(f"Attribute error in on_candle: {str(e)}")
            return None
        except ValueError as e:
            self.logger.error(f"Value error in on_candle: {str(e)}")
            return None
        except KeyError as e:
            self.logger.error(f"Key error in on_candle: {str(e)}")
            return None
        except IndexError as e:
            self.logger.error(f"Index error in on_candle: {str(e)}")
            return None
        
    def calculate_exit_points(self, entry_price, side='BUY'):
        """Calculate stop loss and take profit for arbitrage positions"""
        # For arbitrage, we don't typically use traditional stop-loss/take-profit
        # Instead, we exit when the arbitrage opportunity is complete or timed out
        # But we'll implement a fallback here for safety
        
        fee_pct = self.params['fee_percentage'] / 100
        slippage_pct = self.params['slippage_percentage'] / 100
        
        # Stop loss is just below break-even considering fees
        stop_loss_pct = -(2 * fee_pct + slippage_pct) * 1.5  # 1.5x the transaction costs
        
        if self.current_opportunity:
            # Take profit at the expected arbitrage profit
            take_profit_pct = self.current_opportunity['profit_pct'] / 100
        else:
            # Default take profit
            take_profit_pct = 0.5 / 100  # 0.5%
        
        if side == 'BUY':
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)
        else:  # SELL (short)
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 - take_profit_pct)
        
        return stop_loss, take_profit
