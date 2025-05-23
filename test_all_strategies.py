#!/usr/bin/env python3
"""
Strategy Testing Script

This script runs a comprehensive test of all implemented trading strategies using
both regular and edge case data to validate robustness and error handling.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities
from utils.logger import setup_logger
from utils.history_loader import HistoryLoader

# Import backtest engine
from backtest_engine import BacktestEngine

# Import strategies
from strategies.scalping_strategy import ScalpingStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_following_strategy import TrendFollowingStrategy
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.dca_strategy import DCAStrategy

# Set up logging
def setup_test_logger():
    """Set up logger for testing"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return setup_logger('strategy_test', os.path.join(log_dir, 'strategy_test.log'))

# Create mock data with different market conditions
def create_mock_data(type="normal", periods=1000):
    """
    Create mock price data with different market conditions
    
    Parameters:
    -----------
    type : str
        Type of market data to create:
        - 'normal': Regular price data with some trends and consolidations
        - 'trending': Strong trend with low volatility
        - 'sideways': Sideways market with low volatility
        - 'volatile': High volatility market
        - 'gappy': Market with price gaps
        - 'missing': Data with missing values
        - 'invalid': Data with invalid values
        
    periods : int
        Number of periods to create
        
    Returns:
    --------
    pandas.DataFrame
        Dataframe with OHLCV data
    """
    # Create timestamp index
    base = datetime.now() - timedelta(days=periods)
    timestamps = [base + timedelta(days=i) for i in range(periods)]
    
    # Create base data
    data = {
        'timestamp': timestamps,
        'open': np.zeros(periods),
        'high': np.zeros(periods),
        'low': np.zeros(periods),
        'close': np.zeros(periods),
        'volume': np.zeros(periods)
    }
    
    base_price = 100.0
    price = base_price
    
    # Generate prices based on type
    if type == "normal":
        # Normal market with some trends and consolidations
        for i in range(periods):
            # Add some random walk with slight drift
            change = np.random.normal(0.0001, 0.01)  
            price *= (1 + change)
            
            # Add some swings
            price += np.sin(i / 50) * 5
            
            # Generate OHLC from the price - ensure volatility is positive
            daily_volatility = max(0.001, price * 0.015)  # Ensure positive volatility
            data['open'][i] = price
            data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
            data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
            data['close'][i] = price + np.random.normal(0, daily_volatility/2)
            data['volume'][i] = np.random.gamma(shape=2.0, scale=100000)
            
    elif type == "trending":
        # Strong trend with low volatility
        trend = 0.001  # positive trend
        for i in range(periods):
            price *= (1 + trend + np.random.normal(0, 0.005))
            
            daily_volatility = max(0.001, price * 0.01)  # Ensure positive volatility
            data['open'][i] = price
            data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
            data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
            data['close'][i] = price + np.random.normal(0, daily_volatility/2)
            data['volume'][i] = np.random.gamma(shape=2.0, scale=100000)
            
    elif type == "sideways":
        # Sideways market with low volatility
        for i in range(periods):
            price = base_price + np.random.normal(0, 2)
            
            daily_volatility = max(0.001, price * 0.005)  # Ensure positive volatility
            data['open'][i] = price
            data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
            data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
            data['close'][i] = price + np.random.normal(0, daily_volatility/2)
            data['volume'][i] = np.random.gamma(shape=1.5, scale=80000)
            
    elif type == "volatile":
        # High volatility market
        for i in range(periods):
            price *= (1 + np.random.normal(0, 0.02))
            
            daily_volatility = max(0.001, price * 0.03)  # Ensure positive volatility
            data['open'][i] = price
            data['high'][i] = price + abs(np.random.normal(0, daily_volatility*1.5))
            data['low'][i] = price - abs(np.random.normal(0, daily_volatility*1.5))
            data['close'][i] = price + np.random.normal(0, daily_volatility)
            data['volume'][i] = np.random.gamma(shape=3.0, scale=150000)
            
    elif type == "gappy":
        # Market with price gaps
        for i in range(periods):
            # Add occasional gaps
            if i > 0 and np.random.random() < 0.05:
                price *= (1 + np.random.choice([-1, 1]) * np.random.uniform(0.02, 0.05))
            else:
                price *= (1 + np.random.normal(0, 0.01))
                
            daily_volatility = max(0.001, price * 0.015)  # Ensure positive volatility
            data['open'][i] = price
            data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
            data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
            data['close'][i] = price + np.random.normal(0, daily_volatility/2)
            data['volume'][i] = np.random.gamma(shape=2.0, scale=100000)
            
    elif type == "missing":
        # Data with missing values
        for i in range(periods):
            price *= (1 + np.random.normal(0, 0.01))
            
            # Add some missing data
            if np.random.random() < 0.05:
                data['open'][i] = np.nan
                data['high'][i] = np.nan
                data['low'][i] = np.nan
                data['close'][i] = np.nan
                data['volume'][i] = np.nan
            else:
                daily_volatility = price * 0.015
                data['open'][i] = price
                data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
                data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
                data['close'][i] = price + np.random.normal(0, daily_volatility/2)
                data['volume'][i] = np.random.gamma(shape=2.0, scale=100000)
                
    elif type == "invalid":
        # Data with invalid values
        for i in range(periods):
            price *= (1 + np.random.normal(0, 0.01))
            
            daily_volatility = price * 0.015
            data['open'][i] = price
            
            # Add some invalid data (negative or zero prices)
            if np.random.random() < 0.03:
                if np.random.random() < 0.5:
                    # Negative price
                    data['high'][i] = -price
                    data['low'][i] = -price * 0.9
                else:
                    # Zero price
                    data['high'][i] = 0
                    data['low'][i] = 0
            else:
                data['high'][i] = price + abs(np.random.normal(0, daily_volatility))
                data['low'][i] = price - abs(np.random.normal(0, daily_volatility))
                
            data['close'][i] = price + np.random.normal(0, daily_volatility/2)
            data['volume'][i] = np.random.gamma(shape=2.0, scale=100000)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df

def _run_strategy(strategy_class, strategy_name, params=None, market_types=None, plot=False):
    """
    Test a strategy on various market conditions
    
    Parameters:
    -----------
    strategy_class : class
        Strategy class to test
    strategy_name : str
        Name of the strategy
    params : dict, optional
        Parameters for the strategy
    market_types : list, optional
        List of market types to test, defaults to all
    plot : bool
        Whether to plot results
    """
    logger = logging.getLogger('strategy_test')
    market_types = market_types or ["normal", "trending", "sideways", "volatile", "gappy", "missing", "invalid"]
    
    results = {}
    
    for market_type in market_types:
        logger.info(f"Testing {strategy_name} on {market_type} market")
        
        # Create mock data
        data = create_mock_data(market_type)
        
        # Initialize strategy and backtester
        strategy = strategy_class(strategy_name, params)
        backtester = BacktestEngine(strategy, initial_capital=10000, logger=logger)
        
        # Run backtest
        try:
            result = backtester.run(data)
            results[market_type] = result
            
            logger.info(f"Results for {strategy_name} on {market_type} market:")
            logger.info(f"  Total Return: {result['total_return']:.2f}%")
            logger.info(f"  Win Rate: {result['win_rate']*100:.2f}%")
            logger.info(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
            
            if plot:
                plot_dir = os.path.join('data', 'plots')
                os.makedirs(plot_dir, exist_ok=True)
                
                # Create plot filename
                plot_file = os.path.join(plot_dir, f"{strategy_name}_{market_type}.png")
                backtester.plot_results(save_path=plot_file, show_plot=False)
                
        except Exception as e:
            logger.error(f"Error testing {strategy_name} on {market_type} market: {str(e)}")
            results[market_type] = None
    
    return results

def test_all_strategies():
    """Test all implemented strategies"""
    logger = setup_test_logger()
    logger.info("Starting comprehensive strategy testing")
    
    # Define strategies to test
    strategies = [
        (ScalpingStrategy, "Scalping"),
        (MeanReversionStrategy, "MeanReversion"),
        (TrendFollowingStrategy, "TrendFollowing"),
        (GridTradingStrategy, "GridTrading"),
        (ArbitrageStrategy, "Arbitrage"),
        (DCAStrategy, "DCA")
    ]
    
    all_results = {}
    
    # Test each strategy
    for strategy_class, name in strategies:
        logger.info(f"Testing {name} strategy")
        results = _run_strategy(strategy_class, name, params=None, market_types=None, plot=True)
        all_results[name] = results
    
    # Generate comparative report
    comparative_analysis(all_results, logger)
    
    logger.info("Strategy testing completed")
    return all_results

def comparative_analysis(all_results, logger):
    """Generate comparative analysis of all strategies"""
    logger.info("Performing comparative analysis of strategies")
    
    # Prepare data for comparison
    market_types = ["normal", "trending", "sideways", "volatile", "gappy"]
    metrics = ["total_return", "win_rate", "sharpe_ratio", "max_drawdown_pct"]
    
    # Create comparative tables
    for metric in metrics:
        logger.info(f"\nComparative {metric} across strategies:")
        
        header = f"{'Strategy':<15} | " + " | ".join(f"{m:<10}" for m in market_types)
        logger.info("-" * len(header))
        logger.info(header)
        logger.info("-" * len(header))
        
        for strategy_name, results in all_results.items():
            values = []
            for market_type in market_types:
                if market_type in results and results[market_type]:
                    if metric == "win_rate":
                        # Format win rate as percentage
                        values.append(f"{results[market_type][metric]*100:<10.2f}")
                    else:
                        values.append(f"{results[market_type][metric]:<10.2f}")
                else:
                    values.append(f"{'N/A':<10}")
                    
            logger.info(f"{strategy_name:<15} | " + " | ".join(values))
        
        logger.info("-" * len(header))
    
    # Find best strategy for each market type
    logger.info("\nBest strategy for each market type (based on risk-adjusted return):")
    for market_type in market_types:
        best_sharpe = -float('inf')
        best_strategy = None
        
        for strategy_name, results in all_results.items():
            if market_type in results and results[market_type]:
                sharpe = results[market_type]['sharpe_ratio']
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_strategy = strategy_name
        
        if best_strategy:
            logger.info(f"{market_type:<10}: {best_strategy} (Sharpe: {best_sharpe:.2f})")
        else:
            logger.info(f"{market_type:<10}: No viable strategy found")

if __name__ == "__main__":
    # Run all strategy tests
    results = test_all_strategies()
    
    print("\nTesting completed. Check logs for detailed results.")
