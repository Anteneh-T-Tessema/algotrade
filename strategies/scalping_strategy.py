#!/usr/bin/env python3
"""
Scalping Strategy

This strategy implements a scalping approach for high-frequency trading with small profits.
It looks for short-term price movements and uses multiple technical indicators
to identify quick entry and exit points based on price action, RSI, Bollinger Bands,
MACD, and volume patterns.

The strategy primarily focuses on:
1. Quick entries and exits with tight stop-losses
2. High-probability setups with multiple confirmation indicators
3. Volume-based confirmation of price movements
4. Momentum and price action signals
"""

import logging
import numpy as np
import pandas as pd
import ta
import traceback
from typing import Dict, Optional, Any, List

from strategies.base_strategy import Strategy
from strategies.enhanced_backtesting import BacktestEnhancer

logger = logging.getLogger(__name__)

class ScalpingStrategy(Strategy):
    """
    Scalping strategy for high-frequency trading with small profits.
    This strategy looks for short-term price movements and technical indicators
    to identify entry and exit points with tight risk management.
    """
    
    def __init__(self, name="ScalpingStrategy", params=None):
        """
        Initialize the scalping strategy with parameters.
        
        Parameters:
        -----------
        name : str
            Strategy name identifier
        params : dict, optional
            Configuration parameters for the strategy including:
            - ema_fast: Fast EMA period (default: 8)
            - ema_slow: Slow EMA period (default: 21)
            - rsi_period: RSI calculation period (default: 14)
            - rsi_oversold: RSI oversold threshold (default: 30)
            - rsi_overbought: RSI overbought threshold (default: 70)
            - bollinger_period: Bollinger Bands period (default: 20)
            - bollinger_std: Bollinger Bands standard deviation (default: 2)
            - volume_ma_period: Volume moving average period (default: 20)
            - min_volume_multiplier: Minimum volume ratio to consider high volume (default: 1.5)
            - stop_loss_percentage: Stop loss percentage (default: 0.5%)
            - take_profit_percentage: Take profit percentage (default: 1.0%)
        """
        # Define default parameters
        default_params = {
            'ema_fast': 8,
            'ema_slow': 21,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'bollinger_period': 20,
            'bollinger_std': 2,
            'volume_ma_period': 20,
            'min_volume_multiplier': 1.5,
            'stop_loss_percentage': 0.5,
            'take_profit_percentage': 1.0
        }
        
        # Merge with provided parameters
        self.params = {**default_params, **(params or {})}
        
        super().__init__(name=name, params=self.params)
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Validate parameters
        self._validate_parameters()
        
        # Initialize attributes
        self.candle_history: List[Dict[str, float]] = []
        self.log_counter: int = 0
        self.trade_history: List[Dict[str, Any]] = []
        self.volatility_adjustments: Dict[str, Any] = {}
        self.current_volatility: Optional[float] = None
        self.backtest_enhancer = BacktestEnhancer(self.params.get('enhancer_config', {}))
        self.unrealized_pnl = 0.0 # Initialize unrealized_pnl
        self.drawdown_start_balance = self.params.get('initial_capital', 10000) # Initialize drawdown_start_balance

    def _validate_parameters(self):
        """
        Validate strategy parameters to ensure they are within acceptable ranges.
        Raises warnings for suspicious values that might affect strategy performance.
        """
        try:
            # Validate EMA periods
            if self.params['ema_fast'] <= 0:
                self.logger.warning("Invalid ema_fast value (%s), must be > 0. Using default: 8", self.params['ema_fast'])
                self.params['ema_fast'] = 8
                
            if self.params['ema_slow'] <= 0:
                self.logger.warning("Invalid ema_slow value (%s), must be > 0. Using default: 21", self.params['ema_slow'])
                self.params['ema_slow'] = 21
                
            if self.params['ema_fast'] >= self.params['ema_slow']:
                self.logger.warning("ema_fast (%s) should be less than ema_slow (%s). This may affect crossover signals.", self.params['ema_fast'], self.params['ema_slow'])
            
            # Validate RSI parameters
            if self.params['rsi_period'] <= 0:
                self.logger.warning("Invalid rsi_period value (%s), must be > 0. Using default: 14", self.params['rsi_period'])
                self.params['rsi_period'] = 14
                
            if not (0 <= self.params['rsi_oversold'] <= 100):
                self.logger.warning("Invalid rsi_oversold value (%s), must be between 0-100. Using default: 30", self.params['rsi_oversold'])
                self.params['rsi_oversold'] = 30
                
            if not (0 <= self.params['rsi_overbought'] <= 100):
                self.logger.warning("Invalid rsi_overbought value (%s), must be between 0-100. Using default: 70", self.params['rsi_overbought'])
                self.params['rsi_overbought'] = 70
                
            if self.params['rsi_oversold'] >= self.params['rsi_overbought']:
                self.logger.warning("rsi_oversold (%s) should be less than rsi_overbought (%s). Adjusting values.", self.params['rsi_oversold'], self.params['rsi_overbought'])
                self.params['rsi_oversold'] = 30
                self.params['rsi_overbought'] = 70
                
            # Validate Bollinger Bands parameters
            if self.params['bollinger_period'] <= 0:
                self.logger.warning("Invalid bollinger_period value (%s), must be > 0. Using default: 20", self.params['bollinger_period'])
                self.params['bollinger_period'] = 20
            
            if self.params['bollinger_std'] <= 0:
                self.logger.warning("Invalid bollinger_std value (%s), must be > 0. Using default: 2", self.params['bollinger_std'])
                self.params['bollinger_std'] = 2
                
            # Validate volume parameters
            if self.params['volume_ma_period'] <= 0:
                self.logger.warning("Invalid volume_ma_period value (%s), must be > 0. Using default: 20", self.params['volume_ma_period'])
                self.params['volume_ma_period'] = 20
                
            if self.params['min_volume_multiplier'] <= 0:
                self.logger.warning("Invalid min_volume_multiplier value (%s), must be > 0. Using default: 1.5", self.params['min_volume_multiplier'])
                self.params['min_volume_multiplier'] = 1.5
                
            # Validate risk management parameters
            if self.params['stop_loss_percentage'] <= 0 or self.params['stop_loss_percentage'] > 10:
                self.logger.warning("Unusual stop_loss_percentage value (%s). Should be > 0 and < 10%%. Using default: 0.5", self.params['stop_loss_percentage'])
                self.params['stop_loss_percentage'] = 0.5
                
            if self.params['take_profit_percentage'] <= 0 or self.params['take_profit_percentage'] > 10:
                self.logger.warning("Unusual take_profit_percentage value (%s). Should be > 0 and < 10%%. Using default: 1.0", self.params['take_profit_percentage'])
                self.params['take_profit_percentage'] = 1.0
                
        except KeyError as e:
            self.logger.error("Missing expected parameter key: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except TypeError as e:
            self.logger.error("Parameter type error: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except Exception as e:
            self.logger.error("Error validating parameters: %s", str(e))
            self.logger.debug(traceback.format_exc())
        
    def generate_signal(self, df, market_data=None):
        """
        Generate trading signals based on the strategy rules, incorporating adaptive
        parameters based on volatility and market correlation.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Dataframe with market data and indicators
        market_data : dict or None
            Dictionary of market indicator data for correlation analysis
            
        Returns:
        --------
        str
            'BUY', 'SELL', or 'HOLD' signal
        
        Notes:
        ------
        The strategy generates buy signals when:
        1. Price bounces from lower Bollinger Band with high volume, oversold RSI, and positive MACD crossover
        2. Momentum-based entry with EMA crossover, high volume, and positive momentum
        3. Trend continuation with pullback entry during confirmed uptrend
        
        It generates sell signals when:
        1. Price hits upper Bollinger Band with overbought RSI and negative MACD crossover
        2. Momentum-based exit with downward EMA crossover and negative momentum
        3. Trend reversal signal during confirmed downtrend
        """
        try:
            # Check if dataframe is valid
            if df is None or df.empty:
                self.logger.debug("Empty dataframe provided to generate_signal")
                return 'HOLD'
                
            # Need enough data for indicators
            min_required_candles = 30
            if len(df) < min_required_candles:
                self.logger.debug("Not enough data for signal generation, needed %s candles", min_required_candles)
                return 'HOLD'
            
            # Check for required indicators
            required_indicators = ['ema_fast', 'ema_slow', 'rsi', 'bb_upper', 'bb_lower', 
                                 'macd', 'macd_signal', 'volume', 'volume_ma', 'price_momentum']
            missing_indicators = [ind for ind in required_indicators if ind not in df.columns]
            
            if missing_indicators:
                self.logger.debug("Missing indicators: %s, recalculating", missing_indicators)
                df = self.calculate_indicators(df)
                
                # Check if recalculation succeeded
                still_missing = [ind for ind in required_indicators if ind not in df.columns]
                if still_missing:
                    self.logger.error("Failed to calculate indicators: %s", still_missing)
                    return 'HOLD'
            
            # Get the latest candle data (safely)
            if len(df) < 2:
                self.logger.warning("Need at least 2 candles to detect crossovers")
                return 'HOLD'
                
            try:
                latest = df.iloc[-1]
                prev = df.iloc[-2]
            except IndexError as e:
                self.logger.error("Error accessing dataframe rows: %s", str(e))
                return 'HOLD'
            
            # Check for NaN values in key indicators
            key_indicators = ['ema_fast', 'ema_slow', 'rsi', 'macd', 'macd_signal']
            nan_indicators = [ind for ind in key_indicators if pd.isna(latest[ind])]
            
            if nan_indicators:
                self.logger.debug("NaN values in indicators: %s", nan_indicators)
                return 'HOLD'
            
            # Use adaptive parameters based on current volatility
            adjusted_params = self.adapt_parameters_to_volatility(df)
            current_volatility = getattr(self, 'current_volatility', {'level': 'normal'})
            volatility_adjustments = self.volatility_adjustments if self.volatility_adjustments else {'momentum_threshold': 0.005, 'trend_strength_threshold': 1.0}

            # Get market correlation data if provided
            market_bias = 'neutral'
            correlation_analysis = {}
            if isinstance(market_data, dict) and 'market_bias' in market_data:
                # Direct market bias provided from backtesting or external analysis
                market_bias = market_data['market_bias']
            elif market_data is not None:
                # Calculate market correlation analysis
                correlation_analysis = self.analyze_market_correlation(df, market_data)
                market_bias = correlation_analysis.get('recommendation', 'neutral')
            
            # Enhanced signal logging for adaptive parameters
            self.logger.debug(
                "Adaptive parameters: volatility=%s, momentum threshold=%.4f, market bias=%s",
                current_volatility.get('level', 'normal'),
                volatility_adjustments.get('momentum_threshold', 0.005),
                market_bias
            )
            
            # EMA crossover check
            ema_cross_up = prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']
            ema_cross_down = prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']
            
            # Check distance between EMAs for stronger crossover signal
            ema_distance = abs(latest['ema_fast'] - latest['ema_slow']) / latest['ema_slow'] * 100
            strong_ema_cross = ema_distance > volatility_adjustments.get('trend_strength_threshold', 1.0) * 0.5
            
            # RSI conditions - use adjusted parameters
            rsi_oversold = latest['rsi'] < volatility_adjustments.get('rsi_oversold', adjusted_params['rsi_oversold'])
            rsi_overbought = latest['rsi'] > volatility_adjustments.get('rsi_overbought', adjusted_params['rsi_overbought'])
            rsi_rising = latest['rsi'] > prev['rsi']
            rsi_falling = latest['rsi'] < prev['rsi']
            
            # Detect RSI divergences for stronger signals
            rsi_bullish_divergence = False
            rsi_bearish_divergence = False
            
            if len(df) >= 5:
                # Check last 5 candles for price vs RSI divergence
                lookback = min(5, len(df)-1)
                if df.iloc[-lookback]['low'] < df.iloc[-1]['low'] and df.iloc[-lookback]['rsi'] > df.iloc[-1]['rsi']:
                    rsi_bullish_divergence = True
                if df.iloc[-lookback]['high'] > df.iloc[-1]['high'] and df.iloc[-lookback]['rsi'] < df.iloc[-1]['rsi']:
                    rsi_bearish_divergence = True
            
            # Handle NaN values in Bollinger Bands
            if pd.isna(latest['bb_upper']) or pd.isna(latest['bb_lower']):
                self.logger.debug("NaN values in Bollinger Bands")
                bb_usable = False
                price_above_upper_band = False
                price_below_lower_band = False
                price_near_lower_band = False
                price_near_upper_band = False
            else:
                bb_usable = True
                # Bollinger Bands conditions
                price_above_upper_band = latest['close'] > latest['bb_upper']
                price_below_lower_band = latest['close'] < latest['bb_lower']
                
                # Adjust the "near band" thresholds based on volatility
                lower_band_threshold = 1.01
                upper_band_threshold = 0.99
                
                # Make these thresholds more adaptive in different volatility conditions
                if current_volatility.get('level') == 'high' or current_volatility.get('level') == 'extreme':
                    lower_band_threshold = 1.02  # Wider threshold in high volatility
                    upper_band_threshold = 0.98
                elif current_volatility.get('level') == 'low' or current_volatility.get('level') == 'very_low':
                    lower_band_threshold = 1.005  # Tighter threshold in low volatility
                    upper_band_threshold = 0.995
                
                price_near_lower_band = latest['close'] < latest['bb_lower'] * lower_band_threshold
                price_near_upper_band = latest['close'] > latest['bb_upper'] * upper_band_threshold
                
            # Volume conditions with volatility-adjusted requirements
            volume_requirement = volatility_adjustments.get('volume_requirement', adjusted_params.get('min_volume_multiplier', 1.5))
            if pd.isna(latest['volume']) or pd.isna(latest['volume_ma']) or latest['volume_ma'] == 0:
                high_volume = False
            else:
                high_volume = latest['volume'] > latest['volume_ma'] * volume_requirement
            
            # MACD conditions
            if pd.isna(latest['macd']) or pd.isna(latest['macd_signal']):
                macd_cross_up = False
                macd_cross_down = False
            else:
                macd_cross_up = prev['macd'] <= prev['macd_signal'] and latest['macd'] > latest['macd_signal']
                macd_cross_down = prev['macd'] >= prev['macd_signal'] and latest['macd'] < latest['macd_signal']
                
                # Enhanced MACD analysis - check distance between MACD and signal line 
                # for stronger confirmation
            
            # Price momentum - use adaptive thresholds based on volatility
            if pd.isna(latest['price_momentum']):
                strong_momentum_up = False
                strong_momentum_down = False
            else:
                # Use adaptive momentum threshold from volatility analysis
                momentum_threshold = volatility_adjustments.get('momentum_threshold', 0.005)
                
                # Enhanced momentum detection with adaptive thresholds
                strong_momentum_up = latest['price_momentum'] > momentum_threshold
                strong_momentum_down = latest['price_momentum'] < -momentum_threshold
                
                # Use ROC for additional confirmation if available
                if 'price_roc' in latest.index and not pd.isna(latest['price_roc']):
                    # Scale ROC threshold with volatility
                    roc_threshold = momentum_threshold * 100  # Convert to same scale as ROC
                    strong_momentum_up = strong_momentum_up and latest['price_roc'] > roc_threshold
                    strong_momentum_down = strong_momentum_down and latest['price_roc'] < -roc_threshold
                
                # Use stochastic for additional confirmation
                if 'stoch_k' in latest.index and 'stoch_d' in latest.index and \
                   not pd.isna(latest['stoch_k']) and not pd.isna(latest['stoch_d']):
                    # Stochastic crossovers
                    stoch_cross_up = prev['stoch_k'] <= prev['stoch_d'] and latest['stoch_k'] > latest['stoch_d']
                    stoch_cross_down = prev['stoch_k'] >= prev['stoch_d'] and latest['stoch_k'] < prev['stoch_d']
                    
                    # Use stochastic levels for additional confirmation
                    stoch_oversold = latest['stoch_k'] < 20
                    stoch_overbought = latest['stoch_k'] > 80
                    
                    # Incorporate into momentum detection
                    if stoch_cross_up or stoch_oversold:
                        strong_momentum_up = strong_momentum_up or (latest['price_momentum'] > momentum_threshold/2)
                    if stoch_cross_down or stoch_overbought:
                        strong_momentum_down = strong_momentum_down or (latest['price_momentum'] < -momentum_threshold/2)
            
            # Trend determination with enhanced confirmation
            # Basic trend using EMAs
            uptrend = latest['ema_fast'] > latest['ema_slow'] and latest['close'] > latest['ema_fast']
            downtrend = latest['ema_fast'] < latest['ema_slow'] and latest['close'] < latest['ema_fast']
            
            # Get adaptive trend strength threshold
            trend_strength_threshold = volatility_adjustments.get('trend_strength_threshold', 1.0)
            
            # Advanced trend confirmation with adaptive thresholds
            # Check if price is above/below both EMAs for stronger confirmation
            strong_uptrend = uptrend and latest['close'] > latest['ema_slow']
            strong_downtrend = downtrend and latest['close'] < latest['ema_slow']
            
            # Use distance from EMAs for trend strength confirmation
            if 'dist_from_ema_slow' in latest.index and not pd.isna(latest['dist_from_ema_slow']):
                # If price is far from EMA in trending direction, trend is stronger
                strong_uptrend = strong_uptrend and latest['dist_from_ema_slow'] > trend_strength_threshold
                strong_downtrend = strong_downtrend and latest['dist_from_ema_slow'] < -trend_strength_threshold
            
            # Calculate advanced trend consistency over multiple candles
            trend_consistency = self.calculate_trend_consistency(df)
            
            # Check for required OHLC data
            if 'open' not in df.columns or pd.isna(latest['open']):
                candle_color = None
            else:
                candle_color = "green" if latest['close'] > latest['open'] else "red"
            
            # Enhanced signal generation logic with market bias and volatility adjustments
            
            # ====== SIGNAL FILTERING BASED ON MARKET CONDITIONS ======
            # Apply market bias as a filter with more nuanced approach based on signal strength
            should_consider_buy = True  # Default to considering all signals
            should_consider_sell = True
            
            if market_bias == 'favor_long':
                # Strongly favor long positions, only allow strongest sell signals
                should_consider_sell = False  # Default to no sell signals
                sell_signal_strength_bonus = -1.0  # Negative bonus makes sell signals harder to trigger
                buy_signal_strength_bonus = 1.0   # Positive bonus makes buy signals easier to trigger
            elif market_bias == 'bias_long':
                # Moderately favor long positions
                sell_signal_strength_bonus = -0.5
                buy_signal_strength_bonus = 0.5
            elif market_bias == 'slight_bias_long':
                # Slightly favor long positions
                sell_signal_strength_bonus = -0.2
                buy_signal_strength_bonus = 0.2
            elif market_bias == 'favor_short':
                # Strongly favor short positions
                should_consider_buy = False  # Default to no buy signals
                sell_signal_strength_bonus = 1.0
                buy_signal_strength_bonus = -1.0
            elif market_bias == 'bias_short':
                # Moderately favor short positions
                sell_signal_strength_bonus = 0.5
                buy_signal_strength_bonus = -0.5
            elif market_bias == 'slight_bias_short':
                # Slightly favor short positions
                sell_signal_strength_bonus = 0.2
                buy_signal_strength_bonus = -0.2
            else:  # neutral
                sell_signal_strength_bonus = 0
                buy_signal_strength_bonus = 0
            
            # Calculate signal strength scores for each potential signal type
            buy_signal_strength = 0
            sell_signal_strength = 0
            
            # Apply volatility adjustments for high volatility
            if current_volatility.get('level') in ['high', 'extreme']:
                # In high volatility, require stronger signals
                self.logger.debug("High volatility environment: requiring stronger signals")
                buy_signal_threshold = 2.0  # Higher threshold in high volatility
                sell_signal_threshold = 2.0
                # Add trend consistency requirements
                buy_trend_consistency_req = 1  # More confirmation needed in high volatility
                sell_trend_consistency_req = -1
            elif current_volatility.get('level') in ['low', 'very_low']:
                # In low volatility, more sensitive signals
                self.logger.debug("Low volatility environment: more sensitive to signals")
                buy_signal_threshold = 1.0  # Lower threshold in low volatility
                sell_signal_threshold = 1.0
                # Reduced trend consistency requirements
                buy_trend_consistency_req = -1  # Less confirmation needed
                sell_trend_consistency_req = 1
            else:
                # Normal volatility
                buy_signal_threshold = 1.5
                sell_signal_threshold = 1.5
                buy_trend_consistency_req = 0
                sell_trend_consistency_req = 0
            
            # ====== CALCULATE BUY SIGNAL STRENGTH ======
            if bb_usable and (price_below_lower_band or price_near_lower_band):
                # Bollinger Band support
                buy_signal_strength += 1.0
                if rsi_oversold:
                    buy_signal_strength += 0.5
                if rsi_rising:
                    buy_signal_strength += 0.3
                if high_volume:
                    buy_signal_strength += 0.3
                if macd_cross_up:
                    buy_signal_strength += 0.4
                if rsi_bullish_divergence:
                    buy_signal_strength += 0.5
            
            if ema_cross_up:
                # EMA crossover signal
                buy_signal_strength += 0.8
                if strong_ema_cross:
                    buy_signal_strength += 0.3
                if high_volume:
                    buy_signal_strength += 0.3
                if latest['rsi'] > 30 and latest['rsi'] < 70:  # Not extreme RSI
                    buy_signal_strength += 0.2
                if candle_color == "green":
                    buy_signal_strength += 0.2
                if strong_momentum_up:
                    buy_signal_strength += 0.4
            
            if strong_uptrend and trend_consistency > 0:
                # Trend continuation signal
                buy_signal_strength += 0.7
                if latest['rsi'] < 45:  # Pullback (not oversold but lower RSI)
                    buy_signal_strength += 0.3
                if high_volume:
                    buy_signal_strength += 0.2
                if candle_color == "green":
                    buy_signal_strength += 0.2
                if latest['close'] > prev['close']:  # Current candle is higher
                    buy_signal_strength += 0.2
                if macd_cross_up:
                    buy_signal_strength += 0.3
            
            # ====== CALCULATE SELL SIGNAL STRENGTH ======
            if bb_usable and (price_above_upper_band or price_near_upper_band):
                # Bollinger Band resistance
                sell_signal_strength += 1.0
                if rsi_overbought:
                    sell_signal_strength += 0.5
                if rsi_falling:
                    sell_signal_strength += 0.3
                if high_volume:
                    sell_signal_strength += 0.3
                if macd_cross_down:
                    sell_signal_strength += 0.4
                if rsi_bearish_divergence:
                    sell_signal_strength += 0.5
            
            if ema_cross_down:
                # EMA crossover down
                sell_signal_strength += 0.8
                if strong_ema_cross:
                    sell_signal_strength += 0.3
                if high_volume:
                    sell_signal_strength += 0.3
                if latest['rsi'] > 40:  # Not oversold yet
                    sell_signal_strength += 0.2
                if candle_color == "red":
                    sell_signal_strength += 0.2
                if strong_momentum_down:
                    sell_signal_strength += 0.4
            
            if strong_downtrend and trend_consistency < 0:
                # Trend continuation downward signal
                sell_signal_strength += 0.7
                if latest['rsi'] > 55:  # Not overbought but higher RSI
                    sell_signal_strength += 0.3
                if high_volume:
                    sell_signal_strength += 0.2
                if candle_color == "red":
                    sell_signal_strength += 0.2
                if latest['close'] < prev['close']:  # Current candle is lower
                    sell_signal_strength += 0.2
                if macd_cross_down:
                    sell_signal_strength += 0.3
            
            # Apply market bias adjustments
            buy_signal_strength += buy_signal_strength_bonus
            sell_signal_strength += sell_signal_strength_bonus
            
            # Apply trend consistency adjustments
            if trend_consistency > buy_trend_consistency_req:
                buy_signal_strength += 0.3
            else:
                buy_signal_strength -= 0.3
                
            if trend_consistency < sell_trend_consistency_req:
                sell_signal_strength += 0.3
            else:
                sell_signal_strength -= 0.3
            
            # Log signal strengths for debugging
            self.logger.debug("Signal strengths - BUY: %.2f, SELL: %.2f, Thresholds - BUY: %s, SELL: %s",
                           buy_signal_strength, sell_signal_strength, buy_signal_threshold, sell_signal_threshold)
            
            # ====== GENERATE FINAL SIGNAL ======
            if should_consider_buy and buy_signal_strength >= buy_signal_threshold and buy_signal_strength > sell_signal_strength:
                signal_type = "unknown"
                if bb_usable and (price_below_lower_band or price_near_lower_band):
                    signal_type = "BB support"
                elif ema_cross_up:
                    signal_type = "EMA crossover"
                elif strong_uptrend:
                    signal_type = "trend continuation"
                
                self.logger.info("BUY signal (%s): price=%.2f, RSI=%.2f, strength=%.2f, volatility=%s, market_bias=%s",
                              signal_type, latest['close'], latest['rsi'], buy_signal_strength, current_volatility.get('level'), market_bias)
                return 'BUY'
                
            elif should_consider_sell and sell_signal_strength >= sell_signal_threshold and sell_signal_strength > buy_signal_strength:
                signal_type = "unknown"
                if bb_usable and (price_above_upper_band or price_near_upper_band):
                    signal_type = "BB resistance"
                elif ema_cross_down:
                    signal_type = "EMA crossover"
                elif strong_downtrend:
                    signal_type = "trend continuation"
                
                self.logger.info("SELL signal (%s): price=%.2f, RSI=%.2f, strength=%.2f, volatility=%s, market_bias=%s",
                              signal_type, latest['close'], latest['rsi'], sell_signal_strength, current_volatility.get('level'), market_bias)
                return 'SELL'
                
            # Default: hold position
            return 'HOLD'
            
        except KeyError as e: # Handles missing keys in DataFrame or dicts
            self.logger.error("KeyError in generate_signal: Missing key %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except IndexError as e: # Handles out-of-bounds access in DataFrame
            self.logger.error("IndexError in generate_signal: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except AttributeError as e: # Handles missing attributes
            self.logger.error("AttributeError in generate_signal: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error("TypeError in generate_signal: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except ValueError as e: # Handles issues with data values (e.g. during conversions)
            self.logger.error("ValueError in generate_signal: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'
        except Exception as e:
            self.logger.error("Error generating signal: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 'HOLD'  # Safe default on error
        
    def calculate_exit_points(self, entry_price, side='BUY', atr=None):
        """
        Calculate exit points (stop loss and take profit) based on the entry price.
        
        Parameters:
        -----------
        entry_price : float
            The entry price of the trade
        side : str
            'BUY' or 'SELL' to indicate trade direction
        atr : float, optional
            Average True Range value for dynamic exit points
            
        Returns:
        --------
        tuple
            (stop_loss_price, take_profit_price)
        """
        try:
            # Validate entry price
            if entry_price is None or entry_price <= 0:
                self.logger.error("Invalid entry price: %s", entry_price)
                return None, None
                
            # Validate side
            if side not in ['BUY', 'SELL']:
                self.logger.warning("Invalid side '%s', must be 'BUY' or 'SELL'. Assuming 'BUY'.", side)
                side = 'BUY'
                
            # Get risk parameters with safety checks
            stop_loss_pct = max(0.1, min(5.0, self.params.get('stop_loss_percentage', 0.5))) / 100
            take_profit_pct = max(0.1, min(10.0, self.params.get('take_profit_percentage', 1.0))) / 100
            
            # Use ATR for dynamic stops if available
            if atr is not None and not pd.isna(atr) and atr > 0:
                # Use ATR multipliers for more dynamic exit points
                atr_stop_mult = 1.5
                atr_tp_mult = 3.0  # 2:1 reward-to-risk ratio
                
                if side == 'BUY':
                    stop_loss = entry_price - (atr * atr_stop_mult)
                    take_profit = entry_price + (atr * atr_tp_mult)
                else:  # SELL (short)
                    stop_loss = entry_price + (atr * atr_stop_mult)
                    take_profit = entry_price - (atr * atr_tp_mult)
                    
                self.logger.debug("ATR-based exits - SL: %.4f, TP: %.4f (ATR: %.4f)", stop_loss, take_profit, atr)
            else:
                # Use percentage-based exits
                if side == 'BUY':
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                else:  # SELL (short)
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - take_profit_pct)
                    
                self.logger.debug("Percentage-based exits - SL: %.4f (%.2f%%), TP: %.4f (%.2f%%)", stop_loss, stop_loss_pct*100, take_profit, take_profit_pct*100)
            
            # Validate exit points
            if stop_loss <= 0 or take_profit <= 0:
                self.logger.warning("Invalid exit points calculated: SL=%s, TP=%s", stop_loss, take_profit)
                # Use fallback values
                if side == 'BUY':
                    stop_loss = max(0.1, entry_price * 0.995)
                    take_profit = entry_price * 1.01
                else:
                    stop_loss = entry_price * 1.005
                    take_profit = max(0.1, entry_price * 0.99)
                    
            return stop_loss, take_profit
            
        except TypeError as e:
            self.logger.error("Type error in calculating exit points: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except ValueError as e:
            self.logger.error("Value error in calculating exit points: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except Exception as e:
            self.logger.error("Error calculating exit points: %s", str(e))
            self.logger.debug(traceback.format_exc())
            
            # Return safe default values
            default_sl = entry_price * 0.995 if side == 'BUY' else entry_price * 1.005
            default_tp = entry_price * 1.01 if side == 'BUY' else entry_price * 0.99
            return default_sl, default_tp

    def calculate_trailing_stop(self, current_price, entry_price, max_price, side='BUY', atr=None):
        """
        Calculate a trailing stop loss price based on current market conditions.
        
        Parameters:
        -----------
        current_price : float
            The current market price
        entry_price : float
            The trade entry price
        max_price : float
            The maximum price reached since entry (for long) or minimum for short
        side : str
            'BUY' or 'SELL' to indicate trade direction
        atr : float, optional
            Average True Range value for dynamic trailing stop
            
        Returns:
        --------
        float
            Trailing stop price
        """
        try:
            # Validate inputs
            if None in [current_price, entry_price, max_price] or 0 in [current_price, entry_price, max_price]:
                self.logger.error("Invalid price data for trailing stop: current=%s, entry=%s, max=%s", current_price, entry_price, max_price)
                return None
            
            # Get base trailing parameters
            base_trail_pct = 0.5  # Default 0.5% trailing stop
            
            # If we have ATR, use it for more dynamic trailing
            if atr is not None and not pd.isna(atr) and atr > 0:
                # Higher volatility = wider trailing stop
                atr_multiplier = 2.0
                trail_amount = atr * atr_multiplier
                
                # Calculate percentage equivalent
                trail_pct = (trail_amount / current_price) * 100
                
                # Use a reasonable range for trail percent based on ATR
                trail_pct = max(0.2, min(2.0, trail_pct))
            else:
                # Use base percentage
                trail_pct = base_trail_pct
            
            # Convert to decimal
            trail_pct = trail_pct / 100
            
            # Calculate trailing stop based on side
            if side == 'BUY':
                # For long positions, trail below the max price
                profit_pct = (max_price - entry_price) / entry_price
                
                # Adaptive trailing - increase trail % as profit grows
                if profit_pct > 0.01:  # If more than 1% in profit
                    # Scale the trail percent with profit
                    trail_pct = min(2.0/100, trail_pct * (1 + profit_pct * 5))
                    
                trailing_stop = max_price * (1 - trail_pct)
                
                # Don't move stop below entry price once in profit
                if max_price > entry_price * 1.005:  # Small buffer (0.5%)
                    trailing_stop = max(trailing_stop, entry_price)
                    
            else:  # SELL (short)
                # For short positions, trail above the min price
                profit_pct = (entry_price - max_price) / entry_price
                
                # Adaptive trailing - increase trail % as profit grows
                if profit_pct > 0.01:  # If more than 1% in profit
                    trail_pct = min(2.0/100, trail_pct * (1 + profit_pct * 5))
                    
                trailing_stop = max_price * (1 + trail_pct)
                
                # Don't move stop above entry price once in profit
                if max_price < entry_price * 0.995:  # Small buffer (0.5%)
                    trailing_stop = min(trailing_stop, entry_price)
            
            # Ensure the stop is valid
            if trailing_stop <= 0:
                self.logger.warning("Invalid trailing stop calculated: %s", trailing_stop)
                # Use a fallback calculation
                trailing_stop = max_price * (0.99 if side == 'BUY' else 1.01)
                
            return trailing_stop
            
        except TypeError as e:
            self.logger.error("Type error in calculating trailing stop: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except ValueError as e:
            self.logger.error("Value error in calculating trailing stop: %s", str(e))
            self.logger.debug(traceback.format_exc())
        except Exception as e:
            self.logger.error("Error calculating trailing stop: %s", str(e))
            self.logger.debug(traceback.format_exc())
            
            # Return a safe default
            if side == 'BUY':
                return max_price * 0.99  # 1% below max
            else:
                return max_price * 1.01  # 1% above min

    def calculate_indicators(self, df):
        """
        Calculate technical indicators used by the scalping strategy
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with raw market data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with added indicators including:
            - ema_fast, ema_slow: Fast and slow exponential moving averages
            - rsi: Relative Strength Index
            - bb_upper, bb_middle, bb_lower: Bollinger Bands
            - bb_width: Width of Bollinger Bands (volatility indicator)
            - macd, macd_signal, macd_diff: MACD indicators
            - volume_ma: Volume moving average
            - volume_ratio: Current volume relative to its moving average
            - atr: Average True Range for volatility
            - price_momentum: 3-period price change percentage
            - support, resistance: Dynamic support and resistance levels
            - dist_from_ema_fast, dist_from_ema_slow: Percentage distance from EMAs
        """
        try:
            
            # Check if dataframe is empty or invalid
            if df is None or df.empty:
                self.logger.warning("Empty dataframe provided to calculate_indicators")
                return df
                
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error("Missing required columns: %s", missing_columns)
                return df  # Return original df without calculations
            
            # Make a copy to avoid SettingWithCopyWarning
            df = df.copy()
            
            # Check for invalid data
            if df['close'].isnull().any():
                self.logger.warning("Data contains NaN values in 'close' column")
                # Basic forward fill to handle missing values
                df = df.fillna(method='ffill')
                
            if (df['close'] <= 0).any():
                self.logger.warning("Data contains zero or negative prices")
                # Filter out invalid prices
                df.loc[df['close'] <= 0, 'close'] = df['close'].mean()
            
            try:
                # Ensure float type for calculations
                for col in required_columns:
                    df[col] = df[col].astype(float)
            except Exception as e:
                self.logger.error("Error converting data to float: %s", str(e))
                return df
            
            # Calculate EMAs
            ema_fast = max(1, int(self.params['ema_fast']))
            ema_slow = max(1, int(self.params['ema_slow']))
            
            df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=ema_fast)
            df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=ema_slow)
            
            # Calculate RSI
            rsi_period = max(1, int(self.params['rsi_period']))
            df['rsi'] = ta.momentum.rsi(df['close'], window=rsi_period)
            
            # Calculate Bollinger Bands
            bollinger_period = max(1, int(self.params['bollinger_period']))
            bollinger_std = max(0.1, float(self.params['bollinger_std']))
            
            try:
                indicator_bb = ta.volatility.BollingerBands(
                    df['close'],
                    window=bollinger_period,
                    window_dev=bollinger_std
                )
                
                df['bb_upper'] = indicator_bb.bollinger_hband()
                df['bb_middle'] = indicator_bb.bollinger_mavg()
                df['bb_lower'] = indicator_bb.bollinger_lband()
                df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / (df['bb_middle'] + 1e-10)  # Avoid division by zero
            except Exception as e:
                self.logger.error("Error calculating Bollinger Bands: %s", str(e))
                # Add empty columns to avoid errors
                for col in ['bb_upper', 'bb_middle', 'bb_lower', 'bb_width']:
                    df[col] = np.nan
            
            # Calculate MACD
            try:
                macd_indicator = ta.trend.MACD(df['close'])
                df['macd'] = macd_indicator.macd()
                df['macd_signal'] = macd_indicator.macd_signal()
                df['macd_diff'] = macd_indicator.macd_diff()
            except Exception as e:
                self.logger.error("Error calculating MACD: %s", str(e))
                for col in ['macd', 'macd_signal', 'macd_diff']:
                    df[col] = np.nan
            
            # Calculate Volume Moving Average
            try:
                volume_ma_period = max(1, int(self.params['volume_ma_period']))
                df['volume_ma'] = ta.trend.sma_indicator(df['volume'], window=volume_ma_period)
                df['volume_ratio'] = df['volume'] / (df['volume_ma'] + 1e-10)  # Avoid division by zero
            except Exception as e:
                self.logger.error("Error calculating Volume MA: %s", str(e))
                df['volume_ma'] = np.nan
                df['volume_ratio'] = np.nan
            
            # Calculate ATR for volatility
            try:
                df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
            except Exception as e:
                self.logger.error("Error calculating ATR: %s", str(e))
                df['atr'] = np.nan
            
            # Calculate price momentum
            try:
                # Standard price momentum (percentage change over 3 periods)
                df['price_momentum'] = df['close'].pct_change(3, fill_method=None)
                
                # Enhanced momentum indicators for better signal quality
                # Calculate the rate of change (ROC) - more responsive than pct_change
                df['price_roc'] = ta.momentum.roc(df['close'], window=3)
                
                # Calculate the Stochastic Oscillator for momentum confirmation
                try:
                    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3)
                    df['stoch_k'] = stoch.stoch()
                    df['stoch_d'] = stoch.stoch_signal()
                except Exception as e:
                    self.logger.debug("Error calculating Stochastic: %s", str(e))
                    df['stoch_k'] = np.nan
                    df['stoch_d'] = np.nan
            except Exception as e:
                self.logger.error("Error calculating price momentum: %s", str(e))
                df['price_momentum'] = np.nan
                df['price_roc'] = np.nan
            
            # Calculate support and resistance
            try:
                window = min(10, len(df))  # Ensure window isn't larger than dataframe
                df['support'] = df['low'].rolling(window=window).min()
                df['resistance'] = df['high'].rolling(window=window).max()
            except Exception as e:
                self.logger.error("Error calculating support/resistance: %s", str(e))
                df['support'] = np.nan
                df['resistance'] = np.nan
            
            # Calculate price distance from EMA
            try:
                df['dist_from_ema_fast'] = (df['close'] - df['ema_fast']) / (df['close'] + 1e-10) * 100
                df['dist_from_ema_slow'] = (df['close'] - df['ema_slow']) / (df['close'] + 1e-10) * 100
            except Exception as e:
                self.logger.error("Error calculating EMA distances: %s", str(e))
                df['dist_from_ema_fast'] = np.nan
                df['dist_from_ema_slow'] = np.nan
                
            return df
            
        except KeyError as e: # Handles missing keys in DataFrame
            self.logger.error("KeyError calculating indicators: Missing key %s", str(e))
            self.logger.debug(traceback.format_exc())
            return df
        except ValueError as e: # Handles issues with data values (e.g. during conversions, ta library errors)
            self.logger.error("ValueError calculating indicators: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return df
        except AttributeError as e: # Handles issues with method calls on incorrect types (e.g. if df is None)
            self.logger.error("AttributeError calculating indicators: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return df
        except TypeError as e: # Handles type mismatches in operations
            self.logger.error("TypeError calculating indicators: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return df
        except Exception as e:
            self.logger.error("Error calculating indicators: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return df  # Return original df on error

    def calculate_trend_consistency(self, df, lookback=5):
        """
        Calculate trend consistency over the last n candles.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with market data and indicators
        lookback : int
            Number of previous candles to analyze for trend consistency
            
        Returns:
        --------
        int
            A score representing trend consistency:
            Positive values indicate uptrend consistency (higher is stronger)
            Negative values indicate downtrend consistency (lower is stronger)
            Zero indicates sideways/no consistent trend
        """
        try:
            # Make sure we have enough data
            if len(df) < lookback + 1:
                return 0
                
            # Extract relevant subset of data
            recent_df = df.iloc[-lookback-1:]
            
            # Initialize consistency score
            consistency_score = 0
            
            # Count consecutive candles with same trend characteristics
            for i in range(1, len(recent_df)):
                curr = recent_df.iloc[i]
                prev = recent_df.iloc[i-1]
                
                # Check for basic trend indicators
                if curr['ema_fast'] > curr['ema_slow']:
                    # Uptrend indicators
                    consistency_score += 1
                    
                    # Additional points for strong uptrend characteristics
                    if curr['close'] > curr['ema_fast']:
                        consistency_score += 0.5
                    if curr['close'] > prev['close']:
                        consistency_score += 0.5
                    if curr['dist_from_ema_slow'] > 0:
                        consistency_score += 0.5
                        
                elif curr['ema_fast'] < curr['ema_slow']:
                    # Downtrend indicators
                    consistency_score -= 1
                    
                    # Additional points for strong downtrend characteristics
                    if curr['close'] < curr['ema_fast']:
                        consistency_score -= 0.5
                    if curr['close'] < prev['close']:
                        consistency_score -= 0.5
                    if curr['dist_from_ema_slow'] < 0:
                        consistency_score -= 0.5
                
                # Consider volume confirmation
                if 'volume_ratio' in curr and not pd.isna(curr['volume_ratio']):
                    # High volume in direction of trend adds weight
                    if curr['close'] > prev['close'] and curr['volume_ratio'] > 1.2:
                        consistency_score += 0.5
                    elif curr['close'] < prev['close'] and curr['volume_ratio'] > 1.2:
                        consistency_score -= 0.5
            
            # Normalize to a reasonable range
            return round(consistency_score)
            
        except KeyError as e: # Handles missing keys in DataFrame
            self.logger.error("KeyError in calculate_trend_consistency: Missing key %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 0
        except IndexError as e: # Handles out-of-bounds access in DataFrame
            self.logger.error("IndexError in calculate_trend_consistency: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return 0
        except Exception as e:
            self.logger.error("Error calculating trend consistency: %s", str(e))
            return 0

    def on_candle(self, candle, balance):
        """
        Process a new candle and determine if any action should be taken.
        
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
                self.logger.error("Invalid candle format: %s", type(candle))
                return None
                
            # Convert dict to Series if necessary
            if isinstance(candle, dict):
                candle = pd.Series(candle)
                
            # Check for required price fields
            required_fields = ['open', 'high', 'low', 'close']
            if not all(field in candle.index for field in required_fields):
                self.logger.error("Missing required price fields in candle")
                return None
                
            # Ensure we have numeric price data    
            if not all(isinstance(candle.get(field), (int, float)) for field in required_fields):
                self.logger.error("Non-numeric price data in candle")
                return None
            
            # Track the last N candles for analysis
            if not hasattr(self, 'candle_history'):
                self.candle_history = []
                
            # Add current candle to history (convert to dict to avoid Series reference issues)
            self.candle_history.append({k: candle[k] for k in candle.index if not pd.isna(candle[k])})
            
            # Keep only the most recent 50 candles
            max_history = 50
            if len(self.candle_history) > max_history:
                self.candle_history = self.candle_history[-max_history:]
                
            # Convert history to DataFrame for analysis
            df = pd.DataFrame(self.candle_history)
            
            # Calculate indicators on the entire dataset
            df = self.calculate_indicators(df)
            
            # Ensure indicators were calculated successfully
            if 'ema_fast' not in df.columns or 'ema_slow' not in df.columns:
                self.logger.warning("Failed to calculate indicators")
                return None
                
            # Calculate trend consistency
            trend_consistency = self.calculate_trend_consistency(df)
            
            # Generate signal
            signal = self.generate_signal(df)
            
            # Get current price
            current_price = candle['close']
            
            # Validate price
            if current_price <= 0:
                self.logger.warning("Invalid price: %s", current_price)
                return None
                
            # Validate balance
            if balance <= 0:
                self.logger.warning("Insufficient balance: %s", balance)
                return None
            
            # Get ATR for trailing stops and position sizing if available
            atr = df['atr'].iloc[-1] if 'atr' in df.columns and not pd.isna(df['atr'].iloc[-1]) else None
            
            # Check if we're in a position and should update trailing stops
            if hasattr(self, 'current_position') and self.current_position is not None:
                # Get position details
                position = self.current_position
                
                if hasattr(position, 'entry_price') and hasattr(position, 'side'):
                    entry_price = position.entry_price
                    side = position.side
                    
                    # Track highest/lowest price for trailing stop
                    if not hasattr(position, 'max_price'):
                        position.max_price = current_price
                    else:
                        if side == 'BUY':  # For long positions, track highest price
                            position.max_price = max(position.max_price, current_price)
                        else:  # For short positions, track lowest price
                            position.max_price = min(position.max_price, current_price)
                    
                    # Calculate trailing stop
                    trailing_stop = self.calculate_trailing_stop(
                        current_price, entry_price, position.max_price, side, atr
                    )
                    
                    # Store current trailing stop price for monitoring
                    position.trailing_stop = trailing_stop
                    
                    # Calculate profit/loss percentage
                    if side == 'BUY':
                        profit_pct = (current_price - entry_price) / entry_price * 100
                    else:
                        profit_pct = (entry_price - current_price) / entry_price * 100
                        
                    # Log position status every 10 candles
                    if not hasattr(self, 'log_counter'):
                        self.log_counter = 0
                    
                    self.log_counter += 1
                    if self.log_counter % 10 == 0:
                        self.logger.debug("Position update: %s at %.4f, current: %.4f, P/L: %.2f%%, trailing stop: %.4f",
                                         side, entry_price, current_price, profit_pct, trailing_stop)
                        self.log_counter = 0
                    
                    # Check if trailing stop has been hit
                    if trailing_stop is not None:
                        stop_hit = False
                        
                        # For long positions, exit if price falls below trailing stop
                        if side == 'BUY' and current_price < trailing_stop:
                            stop_hit = True
                            
                        # For short positions, exit if price rises above trailing stop
                        elif side == 'SELL' and current_price > trailing_stop:
                            stop_hit = True
                            
                        if stop_hit:
                            # Trailing stop triggered, exit position
                            self.logger.info("Trailing stop hit: %.4f, current price: %.4f, profit: %.2f%%",
                                           trailing_stop, current_price, profit_pct)
                            return {
                                'action': 'SELL' if side == 'BUY' else 'BUY',  # Opposite of position side
                                'price': current_price,
                                'size': position.size,
                                'reason': 'trailing_stop_exit'
                            }
                    
                    # Check for reversal signals that might warrant early exit
                    # Strong counter-trend signal warrants exit
                    if (side == 'BUY' and signal == 'SELL' and trend_consistency < 0) or \
                       (side == 'SELL' and signal == 'BUY' and trend_consistency > 0):
                        self.logger.info("Exiting %s position due to strong counter trend signal, P/L: %.2f%%", side, profit_pct)
                        return {
                            'action': 'SELL' if side == 'BUY' else 'BUY',  # Opposite of position side
                            'price': current_price,
                            'size': position.size,
                            'reason': 'counter_trend_exit'
                        }
            
            # Execute trading logic based on signal
            if signal == 'BUY' and (not hasattr(self, 'current_position') or self.current_position is None):
                # Check if trend is favorable for entry
                if trend_consistency <= -2:  # Strong downtrend
                    self.logger.debug("Skipping BUY signal due to strong downtrend (consistency: %s)", trend_consistency)
                    return None
                
                # Calculate position size - use 2% of balance per trade as risk
                risk_pct = 0.02  # 2% risk per trade
                
                # Use ATR for dynamic stop loss if available
                if atr is not None and atr > 0:
                    # ATR-based stop loss (1.5 * ATR below entry)
                    stop_loss_amount = atr * 1.5
                    stop_loss_pct = stop_loss_amount / current_price
                else:
                    # Use fixed percentage stop loss from params
                    stop_loss_pct = self.params.get('stop_loss_percentage', 0.5) / 100
                
                # Calculate position size based on risk
                if stop_loss_pct > 0:
                    # Risk-based position sizing
                    risk_amount = balance * risk_pct
                    potential_loss_per_unit = current_price * stop_loss_pct
                    size = risk_amount / potential_loss_per_unit
                else:
                    # Fallback to fixed sizing (1% of balance)
                    size = (balance * 0.01) / current_price
                    
                # Limit position size to reasonable value
                size = min(size, balance * 0.2 / current_price)  # Max 20% of balance
                
                # Create position action with enhanced metadata
                return {
                    'action': 'BUY',
                    'price': current_price,
                    'size': size,
                    'reason': 'signal_entry',
                    'trend_consistency': trend_consistency,
                    'stop_loss_pct': stop_loss_pct * 100,  # Convert to percentage
                    'atr': atr
                }
                
            elif signal == 'SELL' and (not hasattr(self, 'current_position') or self.current_position is None):
                # Check if trend is favorable for entry
                if trend_consistency >= 2:  # Strong uptrend
                    self.logger.debug("Skipping SELL signal due to strong uptrend (consistency: %s)", trend_consistency)
                    return None
                
                # Similar logic for SELL orders (short positions)
                risk_pct = 0.02  # 2% risk per trade
                
                # Use ATR for dynamic stop loss if available
                if atr is not None and atr > 0:
                    # ATR-based stop loss (1.5 * ATR above entry)
                    stop_loss_amount = atr * 1.5
                    stop_loss_pct = stop_loss_amount / current_price
                else:
                    # Use fixed percentage stop loss from params
                    stop_loss_pct = self.params.get('stop_loss_percentage', 0.5) / 100
                
                # Calculate position size based on risk
                if stop_loss_pct > 0:
                    risk_amount = balance * risk_pct
                    potential_loss_per_unit = current_price * stop_loss_pct
                    size = risk_amount / potential_loss_per_unit
                else:
                    size = (balance * 0.01) / current_price
                    
                # Limit position size
                size = min(size, balance * 0.2 / current_price)  # Max 20% of balance
                
                return {
                    'action': 'SELL',
                    'price': current_price,
                    'size': size,
                    'reason': 'signal_entry',
                    'trend_consistency': trend_consistency,
                    'stop_loss_pct': stop_loss_pct * 100,  # Convert to percentage
                    'atr': atr
                }
            
            return None  # No action
            
        except Exception as e:
            self.logger.error("Error in on_candle: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return None

    def analyze_trade_performance(self, entry_price, exit_price, side, trade_duration, trade_reason=""):
        """
        Analyze completed trade performance for strategy improvement.
        
        Parameters:
        -----------
        entry_price : float
            Entry price of the trade
        exit_price : float
            Exit price of the trade
        side : str
            'BUY' or 'SELL' trade direction
        trade_duration : float
            Duration of the trade in seconds/minutes/candles (based on implementation)
        trade_reason : str
            Reason for the trade exit
            
        Returns:
        --------
        dict
            Trade analysis metrics
        """
        try:
            # Calculate basic trade metrics
            if side == 'BUY':
                profit_pct = (exit_price - entry_price) / entry_price * 100
                profitable = exit_price > entry_price
            else:  # SELL (short)
                profit_pct = (entry_price - exit_price) / entry_price * 100
                profitable = exit_price < entry_price
                
            # Calculate reward-to-risk (assuming 2% risk)
            risk_amount = entry_price * (self.params.get('stop_loss_percentage', 0.5) / 100)
            if risk_amount > 0:
                if side == 'BUY':
                    reward_to_risk = abs(exit_price - entry_price) / risk_amount
                else:
                    reward_to_risk = abs(entry_price - exit_price) / risk_amount
            else:
                reward_to_risk = 0
                
            # Calculate trade return metrics
            if trade_duration > 0:
                # Simple ROI per time unit
                roi_per_minute = profit_pct / (trade_duration / 60) if trade_duration >= 60 else profit_pct
            else:
                roi_per_minute = 0
                
            # Create trade summary
            trade_summary = {
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'duration_minutes': trade_duration / 60 if trade_duration >= 60 else trade_duration,
                'profitable': profitable,
                'reward_to_risk': reward_to_risk,
                'roi_per_minute': roi_per_minute,
                'exit_reason': trade_reason
            }
            
            # Log the trade with appropriate level based on profitability
            if profitable:
                self.logger.info("Profitable %s trade: %.2f%%, duration: %.1f minutes", side, profit_pct, trade_summary['duration_minutes'])
            else:
                self.logger.info("Unprofitable %s trade: %.2f%%, duration: %.1f minutes", side, profit_pct, trade_summary['duration_minutes'])
            
            return trade_summary
            
        except Exception as e:
            self.logger.error("Error analyzing trade performance: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return {'error': str(e)}

    def backtest_performance(self, historical_data, market_data=None):
        """
        Run a comprehensive backtest of the strategy on historical data and return detailed performance metrics.
        
        Parameters:
        -----------
        historical_data : pandas.DataFrame
            Historical OHLCV data for backtesting
        market_data : dict, optional
            Dictionary of market indices/indicators DataFrames for correlation analysis
            
        Returns:
        --------
        dict
            Performance metrics including:
            - total_trades: Number of executed trades
            - win_rate: Percentage of profitable trades
            - profit_factor: Gross profit / gross loss
            - avg_profit: Average profit per winning trade
            - avg_loss: Average loss per losing trade
            - max_drawdown: Maximum drawdown percentage
            - sharpe_ratio: Risk-adjusted return metric
            - sortino_ratio: Downside risk-adjusted return metric
            - trade_durations: Average, min and max trade durations
            - monthly_returns: Performance broken down by month
            - win_streak: Longest winning streak
            - loss_streak: Longest losing streak
            - market_condition_performance: Performance breakdown by market condition
            - exit_reason_analysis: Analysis of trade exits by reason
        """
        try:
            self.logger.info("Starting comprehensive strategy backtest")
            
            # Ensure we have required data
            if historical_data is None or len(historical_data) < 50:
                self.logger.error("Insufficient historical data for backtesting")
                return {'error': 'Insufficient data'}
                
            # Initialize tracking variables
            trades = []
            position = None
            balance = 10000  # Starting with $10,000
            initial_balance = balance
            equity_curve = []
            equity_curve_dates = []
            daily_returns = {}  # Track daily returns
            monthly_returns = {}  # Track monthly returns
            volatility_trades = {}  # Track performance by volatility level
            correlation_trades = {}  # Track performance by market correlation
            
            # Win/loss streak tracking
            current_win_streak = 0
            current_loss_streak = 0
            win_streak = 0
            loss_streak = 0
            
            # Track maximum balance to calculate drawdown
            max_balance = balance
            max_drawdown = 0
            drawdown_duration = 0
            max_drawdown_duration = 0
            
            # Calculate indicators once for the entire dataset
            df = self.calculate_indicators(historical_data.copy())
            
            # Process each candle
            for i in range(30, len(df)):  # Skip first 30 candles to ensure indicators are calculated
                # Get current candle slice
                candle_data = df.iloc[:i+1]
                current_candle = candle_data.iloc[-1]
                current_price = current_candle['close']
                current_time = df.index[i] if hasattr(df, 'index') else i
                
                # Apply adaptive parameters to current market conditions
                adjusted_params = self.adapt_parameters_to_volatility(candle_data)
                current_volatility = getattr(self, 'current_volatility', {}).get('level', 'normal')
                
                # If market data provided, analyze broader market correlation
                market_bias = 'neutral'
                if market_data is not None:
                    # Get subset of market data up to current point
                    current_market_data = {}
                    for symbol, symbol_data in market_data.items():
                        if symbol_data is not None and len(symbol_data) > i:
                            current_market_data[symbol] = symbol_data.iloc[:i+1]
                    
                    if current_market_data:
                        correlation_analysis = self.analyze_market_correlation(candle_data, current_market_data)
                        market_bias = correlation_analysis['recommendation']
                
                # Track equity after each candle
                equity_curve.append(balance)
                if hasattr(current_time, 'date'):
                    equity_curve_dates.append(current_time)
                else:
                    equity_curve_dates.append(None)
                
                # Track daily returns
                trade_date = current_time.date() if hasattr(current_time, 'date') else None
                if trade_date is not None:
                    # Initialize daily return tracking if it's a new day
                    if trade_date not in daily_returns:
                        daily_returns[trade_date] = {'start_balance': balance, 'end_balance': balance}
                    else:
                        # Update end balance for this day
                        daily_returns[trade_date]['end_balance'] = balance
                    
                    # Track monthly returns
                    month_key = f"{trade_date.year}-{trade_date.month:02d}"
                    if month_key not in monthly_returns:
                        monthly_returns[month_key] = {'start_balance': balance, 'end_balance': balance, 'trades': 0, 'profitable_trades': 0}
                    else:
                        monthly_returns[month_key]['end_balance'] = balance
                
                # Update drawdown calculation
                if balance > max_balance:
                    max_balance = balance
                    drawdown_duration = 0  # Reset duration since we hit a new high
                    drawdown_start_balance = balance
                else:
                    current_drawdown = (max_balance - balance) / max_balance * 100 if max_balance > 0 else 0
                    max_drawdown = max(max_drawdown, current_drawdown)
                    
                    # Track drawdown duration
                    if current_drawdown > 0:
                        drawdown_duration += 1
                        max_drawdown_duration = max(max_drawdown_duration, drawdown_duration)
                
                # If in position, check for exit
                if position is not None:
                    # Calculate unrealized P&L
                    if position['side'] == 'BUY':
                        self.unrealized_pnl = (current_price - position['entry_price']) * position['size']
                    else:  # SELL (short)
                        self.unrealized_pnl = (position['entry_price'] - current_price) * position['size']
                        
                    # Update position's maximum price for trailing stop
                    if position['side'] == 'BUY':
                        position['max_price'] = max(position['max_price'], current_price)
                    else:  # SELL (short)
                        position['max_price'] = min(position['max_price'], current_price)
                        
                    # Calculate trailing stop with adjusted parameters
                    atr = current_candle['atr'] if 'atr' in current_candle and not pd.isna(current_candle['atr']) else None
                    trailing_stop = self.calculate_trailing_stop(
                        current_price, 
                        position['entry_price'], 
                        position['max_price'], 
                        position['side'], 
                        atr
                    )
                    
                    # Check for trailing stop hit
                    exit_signal = False
                    exit_reason = ""
                    
                    if trailing_stop is not None:
                        if (position['side'] == 'BUY' and current_price < trailing_stop) or \
                           (position['side'] == 'SELL' and current_price > trailing_stop):
                            exit_signal = True
                            exit_reason = "trailing_stop"
                    
                    # Also check for counter-trend signal exit with market correlation bias
                    signal = self.generate_signal(candle_data, {'market_bias': market_bias})
                    trend_consistency = self.calculate_trend_consistency(candle_data)
                    
                    if (position['side'] == 'BUY' and signal == 'SELL' and trend_consistency < 0) or \
                       (position['side'] == 'SELL' and signal == 'BUY' and trend_consistency > 0):
                        exit_signal = True
                        exit_reason = "counter_trend"
                        
                    # Take profit target with dynamic adjustment based on volatility
                    take_profit_pct = adjusted_params.get('take_profit_percentage', 1.0) / 100
                    if position['side'] == 'BUY':
                        take_profit = position['entry_price'] * (1 + take_profit_pct)
                        if current_price >= take_profit:
                            exit_signal = True
                            exit_reason = "take_profit"
                    else:  # SELL
                        take_profit = position['entry_price'] * (1 - take_profit_pct)
                        if current_price <= take_profit:
                            exit_signal = True
                            exit_reason = "take_profit"
                    
                    # Check for time-based exit (after holding for a specific period)
                    max_hold_period = 20  # Maximum candles to hold a position
                    if i - position['entry_index'] >= max_hold_period:
                        exit_signal = True
                        exit_reason = "time_exit"
                            
                    # Exit position if signal triggered
                    if exit_signal:
                        # Calculate trade P&L
                        if position['side'] == 'BUY':
                            trade_pnl = (current_price - position['entry_price']) * position['size']
                        else:  # SELL (short)
                            trade_pnl = (position['entry_price'] - current_price) * position['size']
                            
                        # Update balance
                        balance += trade_pnl
                        
                        # Record trade details
                        trade_duration = i - position['entry_index']
                        
                        trade = {
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'side': position['side'],
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'size': position['size'],
                            'pnl': trade_pnl,
                            'pnl_percentage': (trade_pnl / (position['entry_price'] * position['size'])) * 100,
                            'duration': trade_duration,
                            'exit_reason': exit_reason,
                            'market_volatility': position['market_volatility'],
                            'market_bias': position['market_bias'],
                            'risk_pct': position['risk_pct']
                        }
                        
                        trades.append(trade)
                        
                        # Update streak tracking
                        is_win = trade_pnl > 0
                        
                        if is_win:
                            current_win_streak += 1
                            current_loss_streak = 0
                            win_streak = max(win_streak, current_win_streak)
                        else:
                            current_loss_streak += 1
                            current_win_streak = 0
                            loss_streak = max(loss_streak, current_loss_streak)
                        
                        # Update monthly trade statistics if available
                        if trade_date is not None:
                            month_key = f"{trade_date.year}-{trade_date.month:02d}"
                            if month_key in monthly_returns:
                                monthly_returns[month_key]['trades'] += 1
                                if is_win:
                                    monthly_returns[month_key]['profitable_trades'] += 1
                        
                        # Track trades by market condition
                        # By volatility
                        vol = position['market_volatility']
                        if vol not in volatility_trades:
                            volatility_trades[vol] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
                        volatility_trades[vol]['count'] += 1
                        if is_win:
                            volatility_trades[vol]['wins'] += 1
                        else:
                            volatility_trades[vol]['losses'] += 1
                        volatility_trades[vol]['pnl'] += trade_pnl
                        
                        # By correlation/market bias
                        bias = position['market_bias']
                        if bias not in correlation_trades:
                            correlation_trades[bias] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
                        correlation_trades[bias]['count'] += 1
                        if is_win:
                            correlation_trades[bias]['wins'] += 1
                        else:
                            correlation_trades[bias]['losses'] += 1
                        correlation_trades[bias]['pnl'] += trade_pnl
                        
                        position = None
                        
                # If not in position, check for entry signal
                else:
                    signal = self.generate_signal(candle_data, {'market_bias': market_bias})
                    
                    if signal in ['BUY', 'SELL']:
                        # Calculate position size with adaptive parameters
                        # Adjust risk based on market volatility and correlation
                        base_risk = 0.02  # 2% base risk per trade
                        
                        # Adjust risk based on volatility
                        volatility_level = current_volatility
                        volatility_risk_factor = {
                            'very_low': 1.5,  # More aggressive in low volatility
                            'low': 1.2,
                            'normal': 1.0,
                            'high': 0.8,
                            'extreme': 0.6   # More conservative in high volatility
                        }.get(volatility_level, 1.0)
                        
                        # Adjust risk based on market correlation
                        correlation_risk_factor = 1.0
                        if (signal == 'BUY' and market_bias in ['bias_long', 'favor_long']):
                            correlation_risk_factor = 1.2  # More aggressive when aligned with market
                        elif (signal == 'SELL' and market_bias in ['bias_short', 'favor_short']):
                            correlation_risk_factor = 1.2  # More aggressive when aligned with market
                        elif (signal == 'BUY' and market_bias in ['bias_short', 'favor_short']):
                            correlation_risk_factor = 0.8  # More conservative when against market
                        elif (signal == 'SELL' and market_bias in ['bias_long', 'favor_long']):
                            correlation_risk_factor = 0.8  # More conservative when against market
                        
                        # Calculate final risk percentage
                        risk_pct = base_risk * volatility_risk_factor * correlation_risk_factor
                        risk_pct = min(0.04, max(0.01, risk_pct))  # Limit between 1% and 4%
                        
                        risk_amount = balance * risk_pct
                        atr = current_candle['atr'] if 'atr' in current_candle and not pd.isna(current_candle['atr']) else None
                        
                        # Get stop loss for position sizing
                        stop_loss, _ = self.calculate_exit_points(current_price, signal, atr)
                        
                        if stop_loss is not None:
                            risk_per_unit = abs(current_price - stop_loss)
                            size = risk_amount / risk_per_unit if risk_per_unit > 0 else balance * 0.01 / current_price
                        else:
                            # Default 1% position size if can't calculate risk
                            size = balance * 0.01 / current_price
                            
                        # Limit to max 10% of balance
                        size = min(size, balance * 0.1 / current_price)
                        
                        # Create new position
                        position = {
                            'side': signal,
                            'entry_price': current_price,
                            'size': size,
                            'entry_index': i,
                            'entry_time': current_time,
                            'max_price': current_price,  # For tracking trailing stop
                            'market_volatility': volatility_level,
                            'market_bias': market_bias,
                            'risk_pct': risk_pct * 100  # Store as percentage
                        }
            
            # Close any remaining open position at the end
            if position is not None:
                last_price = df.iloc[-1]['close']
                
                # Calculate trade P&L
                if position['side'] == 'BUY':
                    trade_pnl = (last_price - position['entry_price']) * position['size']
                else:  # SELL (short)
                    trade_pnl = (position['entry_price'] - last_price) * position['size']
                    
                # Update balance
                balance += trade_pnl
                
                # Record trade
                trade_duration = len(df) - 1 - position['entry_index']
                
                trade = {
                    'entry_time': position['entry_time'],
                    'exit_time': df.index[-1] if hasattr(df, 'index') else len(df) - 1,
                    'side': position['side'],
                    'entry_price': position['entry_price'],
                    'exit_price': last_price,
                    'size': position['size'],
                    'pnl': trade_pnl,
                    'pnl_percentage': (trade_pnl / (position['entry_price'] * position['size'])) * 100,
                    'duration': trade_duration,
                    'exit_reason': 'end_of_data',
                    'market_volatility': position['market_volatility'],
                    'market_bias': position['market_bias'],
                    'risk_pct': position['risk_pct']
                }
                
                trades.append(trade)
            
            # Calculate performance metrics using BacktestEnhancer
            if len(trades) == 0:
                self.logger.warning("No trades executed in backtest")
                return {'error': 'No trades executed'}
                
            self.logger.info("Using BacktestEnhancer for comprehensive performance metrics calculation")
                
            # Calculate performance metrics using the enhanced backtesting module
            results = BacktestEnhancer.calculate_performance_metrics(
                trades=trades,
                equity_curve=equity_curve,
                initial_balance=initial_balance,
                daily_returns=daily_returns,
                monthly_returns=monthly_returns,
                volatility_trades=volatility_trades,
                correlation_trades=correlation_trades,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_drawdown_duration
            )
            
            # Extract key metrics for logging
            total_trades = results['total_trades']
            win_rate = results['win_rate']
            net_profit = results['net_profit']
            profit_factor = results['profit_factor']
            expectancy = results['expectancy']
            sharpe_ratio = results['sharpe_ratio']
            sortino_ratio = results['sortino_ratio']
            max_consecutive_wins = results['max_consecutive_wins']
            max_consecutive_losses = results['max_consecutive_losses']
            monthly_performance = results['monthly_performance']
            exit_reasons = results['exit_reason_analysis']
            
            # Store trade history for further analysis
            self.trade_history = trades
            
            # Log comprehensive results summary
            self.logger.info("Backtest completed with %s trades over %s days", total_trades, len(daily_returns) if daily_returns else 'N/A')
            self.logger.info("Win rate: %.2f%%, Profit factor: %.2f, Expectancy: %.2f%%", win_rate, profit_factor, expectancy)
            self.logger.info("Net profit: $%.2f (%.2f%%)", net_profit, results['net_profit_percent'])
            self.logger.info("Max drawdown: %.2f%%, Max drawdown duration: %s candles", max_drawdown, max_drawdown_duration) # max_drawdown from loop
            self.logger.info("Sharpe ratio: %.2f, Sortino ratio: %.2f", sharpe_ratio, sortino_ratio)
            self.logger.info("Win/Loss streak: %s/%s", max_consecutive_wins, max_consecutive_losses)
            
            # Log monthly performance summary
            if monthly_performance:
                self.logger.info("Monthly performance summary:")
                for month, perf in sorted(monthly_performance.items()):
                    self.logger.info("  %s: %.2f%% (Trades: %s, Win rate: %.1f%%)", month, perf['return_pct'], perf['trades'], perf['win_rate'])
            
            # Log exit reason analysis
            self.logger.info("Exit reason analysis:")
            for reason, stats in exit_reasons.items():
                self.logger.info("  %s: %s trades, Win rate: %.1f%%, Avg P/L: $%.2f", reason, stats['count'], stats['win_rate'], stats['avg_pnl'])
            
            # Log volatility analysis
            self.logger.info("Performance by volatility level:")
            for vol, stats in results['volatility_analysis'].items(): # Corrected key here
                self.logger.info("  %s: %s trades, Win rate: %.1f%%, Avg P/L: $%.2f", vol, stats['count'], stats['win_rate'], stats['avg_pnl'])
            
            return results
            
        except Exception as e:
            self.logger.error("Error in backtest: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return {'error': str(e)}

    def adapt_parameters_to_volatility(self, df):
        """
        Dynamically adjust strategy parameters based on current market volatility.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with market data and indicators
            
        Returns:
        --------
        dict
            Dictionary of adjusted parameters
        """
        try:
            # Ensure we have enough data
            if df is None or len(df) < 20:
                self.logger.debug("Not enough data to adapt parameters")
                return self.params.copy()
                
            # Create a copy of current parameters to adjust
            adjusted_params = self.params.copy()
            
            # 1. Calculate volatility metrics using multiple approaches for robustness
            volatility_metrics = {}
            
            # 1.1 ATR-based volatility
            if 'atr' in df.columns and not df['atr'].isnull().all():
                current_atr = df['atr'].iloc[-1]
                atr_ma = df['atr'].rolling(window=20).mean().iloc[-1]
                
                # Normalize ATR as percentage of price
                current_price = df['close'].iloc[-1]
                volatility_metrics['normalized_atr'] = current_atr / current_price * 100 if current_price > 0 else 1
                
                # ATR ratio: current vs historical
                volatility_metrics['atr_ratio'] = current_atr / atr_ma if atr_ma > 0 else 1
            else:
                volatility_metrics['normalized_atr'] = 1
                volatility_metrics['atr_ratio'] = 1
            
            # 1.2 Bollinger Band width as volatility measure
            if 'bb_width' in df.columns and not df['bb_width'].isnull().all():
                current_bb_width = df['bb_width'].iloc[-1]
                avg_bb_width = df['bb_width'].rolling(window=20).mean().iloc[-1]
                
                volatility_metrics['bb_width_ratio'] = current_bb_width / avg_bb_width if avg_bb_width > 0 else 1
            else:
                volatility_metrics['bb_width_ratio'] = 1
                
            # 1.3 Recent price volatility (standard deviation of returns)
            returns = df['close'].pct_change(fill_method=None).dropna()
            if len(returns) >= 20:
                recent_volatility = returns[-20:].std() * 100  # As percentage
                longer_volatility = returns.std() * 100 if len(returns) > 60 else recent_volatility
                
                volatility_metrics['returns_volatility'] = recent_volatility
                volatility_metrics['volatility_ratio'] = recent_volatility / longer_volatility if longer_volatility > 0 else 1
            else:
                volatility_metrics['returns_volatility'] = 1
                volatility_metrics['volatility_ratio'] = 1
            
            # 2. Calculate combined volatility score
            # Weighted average of different volatility metrics
            volatility_score = (
                volatility_metrics['normalized_atr'] * 0.4 +
                volatility_metrics['atr_ratio'] * 0.2 + 
                volatility_metrics['bb_width_ratio'] * 0.2 +
                volatility_metrics['returns_volatility'] * 0.2
            )
            
            # 3. Classify market volatility with more granular levels
            if volatility_score < 0.4:
                volatility = "very_low"
            elif volatility_score < 0.7:
                volatility = "low"
            elif volatility_score < 1.3:
                volatility = "normal"
            elif volatility_score < 2.0:
                volatility = "high"
            else:
                volatility = "extreme"
                
            # 4. Log current volatility state with detailed metrics
            self.logger.debug(
                "Market volatility: %s (score: %.2f, ATR: %.2f%%, BB width ratio: %.2f, Returns vol: %.2f%%)",
                volatility, volatility_score, volatility_metrics['normalized_atr'], volatility_metrics['bb_width_ratio'], volatility_metrics['returns_volatility']
            )
            
            # 5. Adjust parameters based on volatility level
            if volatility == "extreme":
                # In extreme volatility: much wider stops, stronger confirmation required, reduced position size
                adjusted_params['stop_loss_percentage'] = self.params['stop_loss_percentage'] * 1.5
                adjusted_params['take_profit_percentage'] = self.params['take_profit_percentage'] * 1.8
                adjusted_params['bollinger_std'] = min(3.5, self.params['bollinger_std'] * 1.4)  # Much wider bands
                adjusted_params['position_size_factor'] = self.params.get('position_size_factor', 1.0) * 0.6  # Reduce position size
                
                # Adjust volatility-specific parameters
                self.volatility_adjustments = {
                    'momentum_threshold': 0.012,  # Much higher threshold
                    'trend_strength_threshold': 2.0,  # Much stronger trend requirement
                    'rsi_oversold': max(20, self.params['rsi_oversold'] - 10),  # More extreme oversold
                    'rsi_overbought': min(80, self.params['rsi_overbought'] + 10),  # More extreme overbought
                    'volume_requirement': 1.5  # Higher volume requirement
                }
                
            elif volatility == "high":
                # In high volatility: wider stops, stronger confirmation required
                adjusted_params['stop_loss_percentage'] = self.params['stop_loss_percentage'] * 1.3
                adjusted_params['take_profit_percentage'] = self.params['take_profit_percentage'] * 1.4
                adjusted_params['bollinger_std'] = min(3.0, self.params['bollinger_std'] * 1.2)  # Wider bands
                adjusted_params['position_size_factor'] = self.params.get('position_size_factor', 1.0) * 0.8  # Slightly reduced positions
                
                # Adjust volatility-specific parameters
                self.volatility_adjustments = {
                    'momentum_threshold': 0.008,  # Higher threshold
                    'trend_strength_threshold': 1.5,  # Stronger trend requirement
                    'rsi_oversold': max(25, self.params['rsi_oversold'] - 5),  # More extreme oversold
                    'rsi_overbought': min(75, self.params['rsi_overbought'] + 5),  # More extreme overbought
                    'volume_requirement': 1.3  # Higher volume requirement
                }
                
            elif volatility == "low":
                # In low volatility: tighter stops, more sensitive signals
                adjusted_params['stop_loss_percentage'] = max(0.2, self.params['stop_loss_percentage'] * 0.8)
                adjusted_params['take_profit_percentage'] = self.params['take_profit_percentage'] * 0.8  # Lower targets
                adjusted_params['bollinger_std'] = max(1.5, self.params['bollinger_std'] * 0.9)  # Tighter bands
                adjusted_params['position_size_factor'] = self.params.get('position_size_factor', 1.0) * 1.2  # Larger positions
                
                # More sensitive signals
                self.volatility_adjustments = {
                    'momentum_threshold': 0.003,  # Lower threshold
                    'trend_strength_threshold': 0.7,  # Less stringent trend requirement
                    'rsi_oversold': min(35, self.params['rsi_oversold'] + 5),  # Less extreme oversold
                    'rsi_overbought': max(65, self.params['rsi_overbought'] - 5),  # Less extreme overbought
                    'volume_requirement': 1.1  # Lower volume requirement
                }
                
            elif volatility == "very_low":
                # In very low volatility: very tight stops, extremely sensitive signals, larger positions
                adjusted_params['stop_loss_percentage'] = max(0.15, self.params['stop_loss_percentage'] * 0.6)
                adjusted_params['take_profit_percentage'] = self.params['take_profit_percentage'] * 0.6  # Lower targets
                adjusted_params['bollinger_std'] = max(1.2, self.params['bollinger_std'] * 0.8)  # Tighter bands
                adjusted_params['position_size_factor'] = self.params.get('position_size_factor', 1.0) * 1.5  # Much larger positions
                
                # Highly sensitive signals
                self.volatility_adjustments = {
                    'momentum_threshold': 0.002,  # Much lower threshold
                    'trend_strength_threshold': 0.5,  # Much less stringent trend requirement
                    'rsi_oversold': min(40, self.params['rsi_oversold'] + 10),  # Less extreme oversold
                    'rsi_overbought': max(60, self.params['rsi_overbought'] - 10),  # Less extreme overbought
                    'volume_requirement': 1.0  # Minimal volume requirement
                }
                
            else:  # normal volatility
                # Normal volatility: use standard parameters
                self.volatility_adjustments = {
                    'momentum_threshold': 0.005,  # Standard
                    'trend_strength_threshold': 1.0,  # Standard
                    'rsi_oversold': self.params['rsi_oversold'],  # Standard
                    'rsi_overbought': self.params['rsi_overbought'],  # Standard
                    'volume_requirement': 1.2  # Standard volume requirement
                }
            
            # Store volatility metrics for monitoring
            self.current_volatility = {
                'level': volatility,
                'score': volatility_score,
                'metrics': volatility_metrics
            }
            
            return adjusted_params
            
        except Exception as e:
            self.logger.error("Error adapting parameters: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return self.params.copy()  # Return original params on error

    def analyze_market_correlation(self, primary_data, market_data=None):
        """
        Analyze correlation between the primary instrument and broader market indicators.
        
        Parameters:
        -----------
        primary_data : pandas.DataFrame
            DataFrame with OHLCV data for the primary trading instrument
        market_data : dict or None
            Dictionary containing DataFrames for market indices/indicators, where:
            keys are indicator names, values are DataFrames with OHLCV data
            
        Returns:
        --------
        dict
            Dictionary with correlation metrics and trading recommendations
        """
        try:
            # If no market data provided, return empty analysis
            if market_data is None or not isinstance(market_data, dict) or len(market_data) == 0:
                self.logger.debug("No market data provided for correlation analysis")
                return {'correlation': {}, 'recommendation': 'neutral', 'market_trend': 'unknown'}
            
            # Prepare primary data
            if primary_data is None or len(primary_data) < 30:
                self.logger.debug("Not enough primary data for correlation analysis")
                return {'correlation': {}, 'recommendation': 'neutral', 'market_trend': 'unknown'}
            
            # Calculate returns for primary instrument
            primary_returns = primary_data['close'].pct_change(fill_method=None).dropna()
            
            # Analyze correlation with each market indicator
            correlations = {}
            weights = {}
            
            # Define importance weights for different market indicators
            default_weights = {
                'SPY': 0.3,       # S&P 500 ETF
                'QQQ': 0.3,       # NASDAQ ETF
                'VIX': 0.2,       # Volatility index (inverse relationship)
                'BTC': 0.2,       # Bitcoin (if trading crypto)
                'DXY': 0.15,      # Dollar index
                'SECTOR': 0.25    # Relevant sector ETF
            }
            
            # Enhanced correlation analysis across different timeframes
            for indicator_name, indicator_df in market_data.items():
                try:
                    # Calculate returns
                    indicator_returns = indicator_df['close'].pct_change(fill_method=None).dropna()
                    
                    # Align the series to match dates
                    aligned_data = pd.concat([primary_returns, indicator_returns], axis=1, join='inner')
                    aligned_data.columns = ['primary', 'indicator']
                    
                    if len(aligned_data) < 10:
                        self.logger.debug("Not enough aligned data for %s", indicator_name)
                        continue
                    
                    # Calculate correlation over different timeframes
                    # Short term (most recent price action)
                    short_corr = aligned_data[-10:].corr().iloc[0, 1] 
                    
                    # Medium term (recent market behavior)
                    medium_corr = aligned_data[-30:].corr().iloc[0, 1]
                    
                    # Long term (established relationship)
                    long_corr = aligned_data.corr().iloc[0, 1]
                    
                    # Calculate rolling correlation to detect changes in relationship
                    if len(aligned_data) >= 60:
                        roll_corr = aligned_data['primary'].rolling(window=20).corr(aligned_data['indicator'])
                        corr_change = roll_corr.iloc[-1] - roll_corr.iloc[-20]
                    else:
                        corr_change = 0
                    
                    # Handle the case of VIX which typically has inverse correlation
                    if indicator_name == 'VIX':
                        short_corr *= -1
                        medium_corr *= -1
                        long_corr *= -1
                        corr_change *= -1
                    
                    # Store correlation values
                    correlations[indicator_name] = {
                        'short_term': short_corr,
                        'medium_term': medium_corr,
                        'long_term': long_corr,
                        'correlation_trend': corr_change
                    }
                    
                    # Get weight for this indicator
                    weights[indicator_name] = default_weights.get(indicator_name, 0.1)
                    
                    # Log significant correlations
                    if abs(short_corr) > 0.6:
                        self.logger.debug("Strong %s correlation: %.2f (short-term)", indicator_name, short_corr)
                    
                except Exception as e:
                    self.logger.warning("Error calculating correlation for %s: %s", indicator_name, str(e))
            
            if not correlations:
                return {'correlation': {}, 'recommendation': 'neutral', 'market_trend': 'unknown'}
            
            # Calculate market trend score (weighted average of correlations)
            market_trend_score = 0
            total_weight = 0
            
            for indicator, corr_data in correlations.items():
                weight = weights.get(indicator, 0.1)
                # Enhanced scoring with timeframe weighting (emphasize short-term but consider all)
                indicator_score = (
                    corr_data['short_term'] * 0.6 +  # Emphasize recent correlation
                    corr_data['medium_term'] * 0.3 +  # Consider medium term
                    corr_data['long_term'] * 0.1 +    # Consider long term baseline
                    corr_data['correlation_trend'] * 0.3  # Factor in changing correlations
                )
                market_trend_score += indicator_score * weight
                total_weight += weight
            
            # Normalize score
            if total_weight > 0:
                market_trend_score /= total_weight
            
            # Enhanced market trend classification with finer gradations
            if market_trend_score > 0.5:
                market_trend = 'strong_bullish'
            elif market_trend_score > 0.2:
                market_trend = 'bullish'
            elif market_trend_score > 0.05:
                market_trend = 'slight_bullish'
            elif market_trend_score < -0.5:
                market_trend = 'strong_bearish'
            elif market_trend_score < -0.2:
                market_trend = 'bearish'
            elif market_trend_score < -0.05:
                market_trend = 'slight_bearish'
            else:
                market_trend = 'neutral'
            
            # Enhanced trading recommendations based on correlations
            if market_trend == 'strong_bullish':
                recommendation = 'favor_long'
                self.logger.info("Market correlation analysis: Strong bullish market trend detected (score: %.2f), favoring LONG positions", market_trend_score)
            elif market_trend == 'bullish':
                recommendation = 'bias_long'
                self.logger.info("Market correlation analysis: Bullish market trend detected (score: %.2f), bias towards LONG positions", market_trend_score)
            elif market_trend == 'slight_bullish':
                recommendation = 'slight_bias_long'
                self.logger.info("Market correlation analysis: Slight bullish market trend detected (score: %.2f)", market_trend_score)
            elif market_trend == 'strong_bearish':
                recommendation = 'favor_short'
                self.logger.info("Market correlation analysis: Strong bearish market trend detected (score: %.2f), favoring SHORT positions", market_trend_score)
            elif market_trend == 'bearish':
                recommendation = 'bias_short'
                self.logger.info("Market correlation analysis: Bearish market trend detected (score: %.2f), bias towards SHORT positions", market_trend_score)
            elif market_trend == 'slight_bearish':
                recommendation = 'slight_bias_short'
                self.logger.info("Market correlation analysis: Slight bearish market trend detected (score: %.2f)", market_trend_score)
            else:
                recommendation = 'neutral'
                self.logger.info("Market correlation analysis: Neutral market trend detected (score: %.2f)", market_trend_score)
            
            return {
                'correlation': correlations,
                'recommendation': recommendation,
                'market_trend': market_trend
            }
            
        except Exception as e:
            self.logger.error("Error analyzing market correlation: %s", str(e))
            self.logger.debug(traceback.format_exc())
            return {'correlation': {}, 'recommendation': 'neutral', 'market_trend': 'unknown'}