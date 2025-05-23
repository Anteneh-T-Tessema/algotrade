"""
Agentic AI Strategy Manager for Crypto Trading Platform

This service leverages AI to dynamically select, optimize, and execute trading strategies
based on real-time market conditions and performance metrics.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from enum import Enum

# Import strategies
from strategies.base_strategy import Strategy
from strategies.dca_strategy import DCAStrategy
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.scalping_strategy import ScalpingStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.trend_following_strategy import TrendFollowingStrategy

# Import market analysis utilities
from utils.market_analyzer import MarketAnalyzer, MarketType
from utils.performance_metrics import PerformanceMetrics
from utils.risk_management import RiskCalculator, RiskProfile

# Setup logging
logger = logging.getLogger(__name__)

class StrategySelectionMode(Enum):
    """Strategy selection modes"""
    AUTO = "auto"              # AI automatically selects best strategy
    USER_PREFERRED = "user"    # Use user preferences with AI optimization
    FIXED = "fixed"            # Use fixed strategy without AI intervention
    HYBRID = "hybrid"          # Combination of multiple strategies

class AgenticStrategyManager:
    """
    Agentic AI Strategy Manager for dynamic strategy selection and optimization
    
    This class provides the core AI functionality that powers the trading platform's
    autonomous decision-making capabilities. It analyzes market conditions, historical
    performance, and user preferences to determine optimal trading strategies and parameters.
    """
    
    def __init__(self, 
                 config: Dict[str, Any],
                 user_id: str,
                 exchange_connector: Any = None,
                 history_provider: Any = None):
        """
        Initialize the Agentic Strategy Manager
        
        Parameters:
        -----------
        config : Dict[str, Any]
            Configuration parameters
        user_id : str
            ID of the user this manager is operating for
        exchange_connector : Any, optional
            Connector to the exchange for live data and trading
        history_provider : Any, optional
            Provider for historical market data
        """
        self.config = config
        self.user_id = user_id
        self.exchange_connector = exchange_connector
        self.history_provider = history_provider
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer()
        self.performance_metrics = PerformanceMetrics()
        self.risk_calculator = RiskCalculator()
        
        # Strategy registry
        self.strategies = {
            "dca": DCAStrategy,
            "grid": GridTradingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "scalping": ScalpingStrategy,
            "arbitrage": ArbitrageStrategy,
            "trend_following": TrendFollowingStrategy
        }
        
        # Strategy performance cache
        self.strategy_performance = {}
        
        # User preferences
        self.user_preferences = self._load_user_preferences()
        
        # Current active strategies
        self.active_strategies = {}
        
    def _load_user_preferences(self) -> Dict[str, Any]:
        """
        Load user preferences from the database
        
        Returns:
        --------
        Dict[str, Any]
            User preferences including risk profile, preferred strategies, etc.
        """
        # In a production environment, this would fetch from a database
        # For now, return default preferences
        return {
            "risk_profile": "moderate",
            "preferred_strategies": ["dca", "grid"],
            "max_drawdown_pct": 15.0,
            "selection_mode": StrategySelectionMode.AUTO.value,
            "strategy_weights": {
                "dca": 0.3,
                "grid": 0.3,
                "mean_reversion": 0.1,
                "scalping": 0.1,
                "arbitrage": 0.1,
                "trend_following": 0.1
            }
        }
        
    async def analyze_market_conditions(self, 
                                  symbol: str, 
                                  timeframe: str = '1h',
                                  lookback_periods: int = 100) -> Dict[str, Any]:
        """
        Analyze current market conditions to determine market type and volatility
        
        Parameters:
        -----------
        symbol : str
            Trading pair symbol (e.g., 'BTCUSDT')
        timeframe : str, optional
            Candle timeframe (default: '1h')
        lookback_periods : int, optional
            Number of periods to look back (default: 100)
            
        Returns:
        --------
        Dict[str, Any]
            Market conditions including market type, trend, volatility, etc.
        """
        try:
            # Get historical data
            if self.history_provider:
                ohlcv = await self.history_provider.get_historical_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=lookback_periods
                )
            else:
                logger.warning(f"No history provider available. Using mock data.")
                # Generate mock data for testing
                ohlcv = self._generate_mock_data(lookback_periods)
                
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Analyze market conditions
            market_type = self.market_analyzer.determine_market_type(df)
            trend_direction = self.market_analyzer.determine_trend(df)
            volatility = self.market_analyzer.calculate_volatility(df)
            
            # Additional metrics
            volume_profile = self.market_analyzer.analyze_volume_profile(df)
            support_resistance = self.market_analyzer.identify_support_resistance(df)
            liquidity = self.market_analyzer.assess_liquidity(df)
            
            return {
                "market_type": market_type.value,
                "trend_direction": trend_direction,
                "volatility": volatility,
                "volume_profile": volume_profile,
                "support_resistance": support_resistance,
                "liquidity": liquidity,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {str(e)}")
            # Return a default market analysis
            return {
                "market_type": MarketType.NORMAL.value,
                "trend_direction": "neutral",
                "volatility": "medium",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def select_optimal_strategy(self, 
                               symbol: str,
                               timeframe: str = '1h',
                               capital_allocation: float = 1000.0) -> Dict[str, Any]:
        """
        Automatically select the optimal trading strategy based on current market conditions
        
        Parameters:
        -----------
        symbol : str
            Trading pair symbol (e.g., 'BTCUSDT')
        timeframe : str, optional
            Candle timeframe (default: '1h')
        capital_allocation : float, optional
            Amount of capital to allocate to this strategy (default: 1000.0)
            
        Returns:
        --------
        Dict[str, Any]
            Selected strategy details including type, parameters, and expected performance
        """
        try:
            # Get market conditions
            market_conditions = await self.analyze_market_conditions(symbol, timeframe)
            
            # Get historical performance of strategies in similar market conditions
            performance_by_strategy = await self._get_historical_performance(
                market_type=market_conditions["market_type"],
                symbol=symbol
            )
            
            # Apply user preferences and risk profile
            risk_profile = self.risk_calculator.get_risk_profile(self.user_preferences["risk_profile"])
            
            # Selection mode
            selection_mode = StrategySelectionMode(self.user_preferences.get("selection_mode", "auto"))
            
            selected_strategy = None
            
            if selection_mode == StrategySelectionMode.FIXED:
                # User has specified a fixed strategy
                strategy_type = self.user_preferences.get("fixed_strategy", "dca")
                selected_strategy = {
                    "strategy_type": strategy_type,
                    "parameters": self._get_default_parameters(strategy_type, risk_profile)
                }
                
            elif selection_mode == StrategySelectionMode.USER_PREFERRED:
                # Select from user's preferred strategies
                preferred_strategies = self.user_preferences.get("preferred_strategies", ["dca"])
                
                # Filter performance data to preferred strategies
                filtered_performance = {
                    k: v for k, v in performance_by_strategy.items() 
                    if k in preferred_strategies
                }
                
                # Select best performing strategy among preferred
                if filtered_performance:
                    best_strategy = max(filtered_performance, key=lambda k: filtered_performance[k]["sharpe_ratio"])
                    selected_strategy = {
                        "strategy_type": best_strategy,
                        "parameters": self._optimize_parameters(
                            best_strategy, market_conditions, risk_profile
                        )
                    }
                else:
                    # Fall back to first preferred strategy
                    strategy_type = preferred_strategies[0]
                    selected_strategy = {
                        "strategy_type": strategy_type,
                        "parameters": self._get_default_parameters(strategy_type, risk_profile)
                    }
                    
            elif selection_mode == StrategySelectionMode.HYBRID:
                # Implement portfolio approach with multiple strategies
                strategy_weights = self.user_preferences.get("strategy_weights", {})
                selected_strategies = []
                
                for strategy_type, weight in strategy_weights.items():
                    if weight > 0.05:  # Only include strategies with significant weight
                        allocation = capital_allocation * weight
                        selected_strategies.append({
                            "strategy_type": strategy_type,
                            "allocation": allocation,
                            "weight": weight,
                            "parameters": self._optimize_parameters(
                                strategy_type, market_conditions, risk_profile
                            )
                        })
                        
                return {
                    "mode": "hybrid",
                    "strategies": selected_strategies,
                    "market_conditions": market_conditions
                }
                
            else:  # AUTO mode
                # Find best strategy for current market conditions
                best_strategy = self._determine_best_strategy(performance_by_strategy)
                
                # Optimize parameters for current market
                optimal_parameters = self._optimize_parameters(
                    best_strategy, market_conditions, risk_profile
                )
                
                selected_strategy = {
                    "strategy_type": best_strategy,
                    "parameters": optimal_parameters
                }
            
            # Add market conditions and expected performance
            selected_strategy["market_conditions"] = market_conditions
            selected_strategy["expected_performance"] = self._estimate_performance(
                selected_strategy["strategy_type"], 
                selected_strategy["parameters"],
                market_conditions
            )
            
            return selected_strategy
            
        except Exception as e:
            logger.error(f"Error selecting optimal strategy: {str(e)}")
            # Fall back to a safe default strategy (DCA)
            return {
                "strategy_type": "dca",
                "parameters": self._get_default_parameters("dca", "conservative"),
                "error": str(e)
            }
    
    async def _get_historical_performance(self, 
                                    market_type: str, 
                                    symbol: str) -> Dict[str, Dict[str, float]]:
        """
        Get historical performance of strategies in similar market conditions
        
        Parameters:
        -----------
        market_type : str
            Type of market (e.g., 'trending', 'ranging')
        symbol : str
            Trading pair symbol
            
        Returns:
        --------
        Dict[str, Dict[str, float]]
            Performance metrics by strategy
        """
        # In a production environment, this would query a database
        # For now, return mock performance data
        
        # Key is strategy type, value is a dict of performance metrics
        performance = {
            "dca": {
                "win_rate": 75.0,
                "profit_factor": 1.8,
                "sharpe_ratio": 1.2,
                "max_drawdown": 8.0,
                "avg_profit_pct": 12.5
            },
            "grid": {
                "win_rate": 85.0,
                "profit_factor": 2.2,
                "sharpe_ratio": 1.5,
                "max_drawdown": 12.0,
                "avg_profit_pct": 14.0
            },
            "mean_reversion": {
                "win_rate": 65.0,
                "profit_factor": 1.5,
                "sharpe_ratio": 0.9,
                "max_drawdown": 15.0,
                "avg_profit_pct": 10.0
            },
            "scalping": {
                "win_rate": 60.0,
                "profit_factor": 1.3,
                "sharpe_ratio": 0.8,
                "max_drawdown": 18.0,
                "avg_profit_pct": 8.0
            },
            "arbitrage": {
                "win_rate": 90.0,
                "profit_factor": 2.5,
                "sharpe_ratio": 1.8,
                "max_drawdown": 6.0,
                "avg_profit_pct": 7.0
            },
            "trend_following": {
                "win_rate": 70.0,
                "profit_factor": 2.0,
                "sharpe_ratio": 1.4,
                "max_drawdown": 14.0,
                "avg_profit_pct": 16.0
            }
        }
        
        # Adjust metrics based on market type
        if market_type == "trending":
            performance["trend_following"]["sharpe_ratio"] *= 1.3
            performance["dca"]["sharpe_ratio"] *= 1.1
        elif market_type == "ranging":
            performance["grid"]["sharpe_ratio"] *= 1.3
            performance["mean_reversion"]["sharpe_ratio"] *= 1.2
        elif market_type == "volatile":
            performance["dca"]["sharpe_ratio"] *= 1.2
            performance["grid"]["sharpe_ratio"] *= 1.1
        elif market_type == "gappy":
            performance["dca"]["sharpe_ratio"] *= 1.1
            performance["arbitrage"]["sharpe_ratio"] *= 0.8
        
        return performance
    
    def _determine_best_strategy(self, performance_by_strategy: Dict[str, Dict[str, float]]) -> str:
        """
        Determine the best strategy based on performance metrics
        
        Parameters:
        -----------
        performance_by_strategy : Dict[str, Dict[str, float]]
            Performance metrics by strategy
            
        Returns:
        --------
        str
            The best strategy type
        """
        # Calculate a composite score based on multiple metrics
        scores = {}
        
        for strategy, metrics in performance_by_strategy.items():
            # Weighted score calculation
            score = (
                metrics["sharpe_ratio"] * 0.4 +
                metrics["win_rate"] / 100 * 0.2 +
                metrics["profit_factor"] * 0.2 -
                metrics["max_drawdown"] / 100 * 0.2
            )
            scores[strategy] = score
        
        # Return strategy with highest score
        return max(scores, key=scores.get)
    
    def _optimize_parameters(self, 
                            strategy_type: str, 
                            market_conditions: Dict[str, Any],
                            risk_profile: str) -> Dict[str, Any]:
        """
        Optimize strategy parameters based on market conditions and risk profile
        
        Parameters:
        -----------
        strategy_type : str
            Type of strategy to optimize
        market_conditions : Dict[str, Any]
            Current market conditions
        risk_profile : str
            User's risk profile
            
        Returns:
        --------
        Dict[str, Any]
            Optimized parameters for the strategy
        """
        # Get default parameters for the strategy
        params = self._get_default_parameters(strategy_type, risk_profile)
        
        # Adjust parameters based on market conditions
        market_type = market_conditions["market_type"]
        trend = market_conditions["trend_direction"]
        volatility = market_conditions["volatility"]
        
        # Strategy-specific optimizations
        if strategy_type == "dca":
            if market_type == "volatile":
                # Increase frequency and reduce size for volatile markets
                params["interval_hours"] = max(12, params["interval_hours"] // 2)
                params["buy_amount"] = params["buy_amount"] * 0.8
                params["dip_threshold_pct"] = params["dip_threshold_pct"] * 1.5
            
            elif market_type == "trending":
                # Adjust based on trend direction
                if trend == "bullish":
                    params["take_profit_pct"] = params["take_profit_pct"] * 1.2
                else:
                    params["dip_threshold_pct"] = params["dip_threshold_pct"] * 0.8
        
        elif strategy_type == "grid":
            if market_type == "ranging":
                # Tighter grid for ranging markets
                params["grid_levels"] = min(20, params["grid_levels"] * 1.5)
                params["grid_size_pct"] = params["grid_size_pct"] * 0.8
            
            elif market_type == "volatile":
                # Wider grid for volatile markets
                params["grid_size_pct"] = params["grid_size_pct"] * 1.5
                params["dynamic_grid"] = True
        
        elif strategy_type == "mean_reversion":
            if volatility == "high":
                # Adjust thresholds for high volatility
                params["entry_std_dev"] = params["entry_std_dev"] * 1.2
                params["exit_std_dev"] = params["exit_std_dev"] * 1.2
        
        # Apply risk profile adjustments
        self._apply_risk_adjustments(params, risk_profile)
        
        return params
    
    def _get_default_parameters(self, strategy_type: str, risk_profile: str) -> Dict[str, Any]:
        """
        Get default parameters for a strategy with risk profile adjustments
        
        Parameters:
        -----------
        strategy_type : str
            Type of strategy
        risk_profile : str
            User's risk profile
            
        Returns:
        --------
        Dict[str, Any]
            Default parameters for the strategy
        """
        # Base parameters by strategy type
        if strategy_type == "dca":
            params = {
                'interval_hours': 24,
                'buy_amount': 100,
                'dip_threshold_pct': 5.0,
                'dip_multiplier': 1.5,
                'use_rsi': True,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_multiplier': 1.3,
                'take_profit_pct': 20.0,
                'max_positions': 10,
                'merge_positions': True
            }
        
        elif strategy_type == "grid":
            params = {
                'grid_levels': 10,
                'grid_size_pct': 1.0,
                'total_investment': 1000,
                'upper_limit_pct': 10.0,
                'lower_limit_pct': 10.0,
                'reference_price_type': 'current',
                'reference_ma_period': 20,
                'dynamic_grid': False,
                'rebalance_frequency': 24,
                'partial_fill': True,
                'position_size_pct': 10.0
            }
            
        elif strategy_type == "mean_reversion":
            params = {
                'lookback_period': 20,
                'entry_std_dev': 2.0,
                'exit_std_dev': 0.5,
                'stop_loss_std_dev': 4.0,
                'position_size_pct': 10.0,
                'max_positions': 3,
                'use_bollinger': True,
                'use_rsi': True,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            
        elif strategy_type == "scalping":
            params = {
                'profit_target_pct': 0.5,
                'stop_loss_pct': 0.3,
                'max_spread_pct': 0.1,
                'min_volume': 100000,
                'timeout_minutes': 30,
                'position_size_pct': 15.0,
                'use_orderbook': True,
                'min_bid_ask_ratio': 0.8,
                'use_momentum': True,
                'momentum_period': 10
            }
            
        elif strategy_type == "arbitrage":
            params = {
                'min_profit_pct': 0.5,
                'max_exposure_pct': 25.0,
                'scan_interval_seconds': 10,
                'execution_timeout_seconds': 5,
                'max_slippage_pct': 0.2,
                'use_triangular': True,
                'use_cross_exchange': True,
                'max_open_arbitrage': 5
            }
            
        elif strategy_type == "trend_following":
            params = {
                'fast_ma_period': 9,
                'slow_ma_period': 21,
                'signal_period': 9,
                'trend_strength_threshold': 25,
                'position_size_pct': 20.0,
                'trailing_stop_pct': 5.0,
                'profit_target_pct': 15.0,
                'max_positions': 2,
                'use_adx': True,
                'adx_threshold': 25
            }
            
        else:
            # Default to DCA as a safe fallback
            logger.warning(f"Unknown strategy type: {strategy_type}. Using DCA defaults.")
            return self._get_default_parameters("dca", risk_profile)
        
        # Apply risk profile adjustments
        self._apply_risk_adjustments(params, risk_profile)
        
        return params
    
    def _apply_risk_adjustments(self, params: Dict[str, Any], risk_profile: str) -> None:
        """
        Apply risk profile adjustments to strategy parameters
        
        Parameters:
        -----------
        params : Dict[str, Any]
            Strategy parameters to adjust
        risk_profile : str
            User's risk profile
            
        Returns:
        --------
        None
            Parameters are modified in-place
        """
        if risk_profile == "conservative":
            # Reduce position sizes
            if "position_size_pct" in params:
                params["position_size_pct"] *= 0.7
                
            # Reduce buy amounts
            if "buy_amount" in params:
                params["buy_amount"] *= 0.8
                
            # Tighter stop losses
            if "stop_loss_pct" in params:
                params["stop_loss_pct"] *= 0.8
                
            # Lower profit targets (get out earlier)
            if "profit_target_pct" in params:
                params["profit_target_pct"] *= 0.9
                
            # Lower exposure
            if "max_exposure_pct" in params:
                params["max_exposure_pct"] *= 0.7
                
        elif risk_profile == "aggressive":
            # Increase position sizes
            if "position_size_pct" in params:
                params["position_size_pct"] *= 1.3
                
            # Increase buy amounts
            if "buy_amount" in params:
                params["buy_amount"] *= 1.2
                
            # Wider stop losses
            if "stop_loss_pct" in params:
                params["stop_loss_pct"] *= 1.2
                
            # Higher profit targets
            if "profit_target_pct" in params:
                params["profit_target_pct"] *= 1.2
                
            # Higher exposure
            if "max_exposure_pct" in params:
                params["max_exposure_pct"] *= 1.3
                
        # 'moderate' risk profile uses default parameters
        
    def _estimate_performance(self, 
                             strategy_type: str, 
                             parameters: Dict[str, Any], 
                             market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate expected performance of a strategy with given parameters
        
        Parameters:
        -----------
        strategy_type : str
            Type of strategy
        parameters : Dict[str, Any]
            Strategy parameters
        market_conditions : Dict[str, Any]
            Current market conditions
            
        Returns:
        --------
        Dict[str, Any]
            Estimated performance metrics
        """
        # This is a simplified performance estimation
        # In a production environment, this would use ML models or historical simulation
        
        market_type = market_conditions["market_type"]
        
        # Base metrics by strategy and market type
        if strategy_type == "dca":
            if market_type == "trending":
                metrics = {
                    "win_rate": 82.0,
                    "avg_profit_pct": 15.0,
                    "max_drawdown_pct": 8.0,
                    "sharpe_ratio": 1.4,
                    "expected_monthly_return": 3.5,
                    "confidence": "high"
                }
            elif market_type == "volatile":
                metrics = {
                    "win_rate": 75.0,
                    "avg_profit_pct": 12.0,
                    "max_drawdown_pct": 12.0,
                    "sharpe_ratio": 1.1,
                    "expected_monthly_return": 4.0,
                    "confidence": "medium"
                }
            else:  # normal, ranging, gappy, etc.
                metrics = {
                    "win_rate": 78.0,
                    "avg_profit_pct": 10.0,
                    "max_drawdown_pct": 10.0,
                    "sharpe_ratio": 1.2,
                    "expected_monthly_return": 2.8,
                    "confidence": "medium"
                }
        
        elif strategy_type == "grid":
            if market_type == "ranging":
                metrics = {
                    "win_rate": 88.0,
                    "avg_profit_pct": 12.0,
                    "max_drawdown_pct": 7.0,
                    "sharpe_ratio": 1.6,
                    "expected_monthly_return": 3.0,
                    "confidence": "high"
                }
            elif market_type == "trending":
                metrics = {
                    "win_rate": 70.0,
                    "avg_profit_pct": 8.0,
                    "max_drawdown_pct": 15.0,
                    "sharpe_ratio": 0.9,
                    "expected_monthly_return": 2.0,
                    "confidence": "low"
                }
            else:
                metrics = {
                    "win_rate": 80.0,
                    "avg_profit_pct": 9.0,
                    "max_drawdown_pct": 10.0,
                    "sharpe_ratio": 1.2,
                    "expected_monthly_return": 2.5,
                    "confidence": "medium"
                }
        
        # Similar patterns for other strategies...
        
        else:
            # Default metrics for unknown strategies
            metrics = {
                "win_rate": 70.0,
                "avg_profit_pct": 8.0,
                "max_drawdown_pct": 12.0,
                "sharpe_ratio": 1.0,
                "expected_monthly_return": 2.0,
                "confidence": "low"
            }
        
        # Add timestamp and strategy info
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["strategy_type"] = strategy_type
        
        return metrics
    
    def _generate_mock_data(self, lookback_periods: int) -> List[List[float]]:
        """
        Generate mock OHLCV data for testing
        
        Parameters:
        -----------
        lookback_periods : int
            Number of periods to generate
            
        Returns:
        --------
        List[List[float]]
            Mock OHLCV data
        """
        data = []
        price = 10000.0  # Starting price
        
        for i in range(lookback_periods):
            timestamp = int((datetime.now() - timedelta(hours=lookback_periods-i)).timestamp() * 1000)
            
            # Random price movement
            change_pct = np.random.normal(0, 0.015)  # Mean 0, std 1.5%
            price *= (1 + change_pct)
            
            # Generate OHLCV
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = price * (1 + np.random.normal(0, 0.003))
            close = price
            volume = np.random.gamma(shape=2.0, scale=50) * price
            
            data.append([timestamp, open_price, high, low, close, volume])
            
        return data
    
    async def create_strategy_instance(self, strategy_type: str, parameters: Dict[str, Any]) -> Strategy:
        """
        Create a strategy instance with the specified parameters
        
        Parameters:
        -----------
        strategy_type : str
            Type of strategy to create
        parameters : Dict[str, Any]
            Strategy parameters
            
        Returns:
        --------
        Strategy
            Instantiated strategy object
        """
        if strategy_type not in self.strategies:
            logger.error(f"Unknown strategy type: {strategy_type}")
            raise ValueError(f"Unknown strategy type: {strategy_type}")
            
        strategy_class = self.strategies[strategy_type]
        strategy_name = f"{strategy_type.capitalize()}_{self.user_id[:8]}"
        
        return strategy_class(name=strategy_name, params=parameters)
    
    async def start_strategy(self, 
                      strategy_id: str,
                      strategy_type: str,
                      parameters: Dict[str, Any],
                      symbol: str,
                      timeframe: str = '1h') -> Dict[str, Any]:
        """
        Start a trading strategy
        
        Parameters:
        -----------
        strategy_id : str
            Unique ID for this strategy instance
        strategy_type : str
            Type of strategy to start
        parameters : Dict[str, Any]
            Strategy parameters
        symbol : str
            Trading pair symbol
        timeframe : str, optional
            Candle timeframe (default: '1h')
            
        Returns:
        --------
        Dict[str, Any]
            Strategy status information
        """
        try:
            # Create strategy instance
            strategy = await self.create_strategy_instance(strategy_type, parameters)
            
            # Store in active strategies
            self.active_strategies[strategy_id] = {
                "strategy": strategy,
                "type": strategy_type,
                "symbol": symbol,
                "timeframe": timeframe,
                "parameters": parameters,
                "started_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            logger.info(f"Started strategy {strategy_id} ({strategy_type}) for symbol {symbol}")
            
            # In a production environment, this would connect to the exchange
            # and start processing market data and trade signals
            
            return {
                "strategy_id": strategy_id,
                "status": "started",
                "type": strategy_type,
                "symbol": symbol,
                "parameters": parameters,
                "started_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting strategy: {str(e)}")
            return {
                "strategy_id": strategy_id,
                "status": "error",
                "error": str(e)
            }
    
    async def stop_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Stop a running strategy
        
        Parameters:
        -----------
        strategy_id : str
            ID of the strategy to stop
            
        Returns:
        --------
        Dict[str, Any]
            Strategy status information
        """
        if strategy_id not in self.active_strategies:
            return {
                "strategy_id": strategy_id,
                "status": "not_found"
            }
            
        try:
            strategy_info = self.active_strategies[strategy_id]
            
            # Update status
            strategy_info["status"] = "stopped"
            strategy_info["stopped_at"] = datetime.now().isoformat()
            
            # In a production environment, this would clean up resources,
            # close positions if needed, and disconnect from the exchange
            
            logger.info(f"Stopped strategy {strategy_id}")
            
            # Remove from active strategies
            self.active_strategies.pop(strategy_id)
            
            return {
                "strategy_id": strategy_id,
                "status": "stopped",
                "stopped_at": strategy_info["stopped_at"]
            }
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_id}: {str(e)}")
            return {
                "strategy_id": strategy_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_strategy_status(self, strategy_id: str = None) -> Dict[str, Any]:
        """
        Get status of one or all active strategies
        
        Parameters:
        -----------
        strategy_id : str, optional
            ID of the strategy to query, or None for all strategies
            
        Returns:
        --------
        Dict[str, Any]
            Strategy status information
        """
        if strategy_id:
            if strategy_id in self.active_strategies:
                strategy_info = self.active_strategies[strategy_id]
                return {
                    "strategy_id": strategy_id,
                    "status": strategy_info["status"],
                    "type": strategy_info["type"],
                    "symbol": strategy_info["symbol"],
                    "started_at": strategy_info["started_at"]
                }
            else:
                return {
                    "strategy_id": strategy_id,
                    "status": "not_found"
                }
        else:
            # Return all active strategies
            result = []
            for sid, info in self.active_strategies.items():
                result.append({
                    "strategy_id": sid,
                    "status": info["status"],
                    "type": info["type"],
                    "symbol": info["symbol"],
                    "started_at": info["started_at"]
                })
            return {
                "strategies": result,
                "count": len(result)
            }
            
    async def process_candle(self, 
                      strategy_id: str,
                      candle: Dict[str, Any],
                      balance: float) -> Dict[str, Any]:
        """
        Process a new candle with the specified strategy
        
        Parameters:
        -----------
        strategy_id : str
            ID of the strategy to use
        candle : Dict[str, Any]
            Candle data
        balance : float
            Available balance
            
        Returns:
        --------
        Dict[str, Any]
            Action to take (if any)
        """
        if strategy_id not in self.active_strategies:
            logger.warning(f"Strategy {strategy_id} not found")
            return {"error": "Strategy not found"}
            
        try:
            strategy_info = self.active_strategies[strategy_id]
            strategy = strategy_info["strategy"]
            
            # Convert candle to pandas Series
            candle_series = pd.Series({
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["volume"],
                "timestamp": pd.Timestamp(candle["timestamp"])
            })
            
            # Process candle
            action = strategy.on_candle(candle_series, balance)
            
            if action:
                # Log the action
                logger.info(
                    f"Strategy {strategy_id} generated action: {action['action']} "
                    f"{action.get('size', 0)} {strategy_info['symbol']} at {action.get('price', 0)}"
                )
                
                # In a production environment, this would execute the trade
                # via the exchange connector
                
                return {
                    "strategy_id": strategy_id,
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "strategy_id": strategy_id,
                    "action": None,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing candle with strategy {strategy_id}: {str(e)}")
            return {
                "strategy_id": strategy_id,
                "error": str(e)
            }
            
    async def update_user_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user preferences
        
        Parameters:
        -----------
        preferences : Dict[str, Any]
            Updated preferences
            
        Returns:
        --------
        Dict[str, Any]
            Updated user preferences
        """
        try:
            # Validate preferences
            valid_risk_profiles = ["conservative", "moderate", "aggressive"]
            if "risk_profile" in preferences and preferences["risk_profile"] not in valid_risk_profiles:
                return {
                    "error": f"Invalid risk profile. Must be one of: {valid_risk_profiles}"
                }
                
            # Update preferences
            self.user_preferences.update(preferences)
            
            # In a production environment, this would persist to a database
            
            return {
                "success": True,
                "preferences": self.user_preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def backtest_strategy(self,
                         strategy_type: str,
                         parameters: Dict[str, Any],
                         symbol: str,
                         timeframe: str = '1d',
                         start_date: str = None,
                         end_date: str = None,
                         initial_capital: float = 10000) -> Dict[str, Any]:
        """
        Backtest a strategy with the specified parameters
        
        Parameters:
        -----------
        strategy_type : str
            Type of strategy to backtest
        parameters : Dict[str, Any]
            Strategy parameters
        symbol : str
            Trading pair symbol
        timeframe : str, optional
            Candle timeframe (default: '1d')
        start_date : str, optional
            Start date for backtest (default: 1 year ago)
        end_date : str, optional
            End date for backtest (default: now)
        initial_capital : float, optional
            Initial capital for backtest (default: 10000)
            
        Returns:
        --------
        Dict[str, Any]
            Backtest results
        """
        # This would integrate with your existing backtesting engine
        # For now, return mock results
        
        return {
            "strategy_type": strategy_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
            "initial_capital": initial_capital,
            "final_capital": 12500.75,
            "profit_loss": 2500.75,
            "profit_loss_pct": 25.01,
            "max_drawdown_pct": 15.3,
            "sharpe_ratio": 1.35,
            "total_trades": 42,
            "win_rate": 73.8,
            "average_profit": 120.5,
            "average_loss": 45.8,
            "profit_factor": 2.1,
            "status": "completed"
        }
