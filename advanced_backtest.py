#!/usr/bin/env python3
"""
Enhanced Backtesting Script

This script provides comprehensive backtesting functionality for all trading strategies:
- Scalping
- Mean Reversion
- Trend Following
- Grid Trading
- Arbitrage
- Dollar-Cost Averaging (DCA)

Features:
- Performance metrics and equity curves
- Strategy comparison
- Position tracking
- Walk-forward testing
- Parameter optimization
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Tuple, Optional

# Add project root to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities
from utils.logger import setup_logger
from utils.history_loader import HistoryLoader

# Import backtest engine
from backtest_engine import BacktestEngine, run_walk_forward

# Import strategies
from strategies.scalping_strategy import ScalpingStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.trend_following_strategy import TrendFollowingStrategy
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.dca_strategy import DCAStrategy

# Create directories if they don't exist
def ensure_directories():
    """Create necessary directories for output"""
    dirs = ['data', 'logs', 'data/plots', 'data/results']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

# Strategy factory for creating strategy instances
def create_strategy(strategy_name, params=None):
    """
    Create a strategy instance based on name
    
    Parameters:
    -----------
    strategy_name : str
        Name of the strategy to create
    params : dict, optional
        Parameters for the strategy
    
    Returns:
    --------
    Strategy
        Strategy instance
    """
    strategies = {
        'scalping': ScalpingStrategy,
        'mean_reversion': MeanReversionStrategy,
        'trend_following': TrendFollowingStrategy,
        'grid_trading': GridTradingStrategy,
        'arbitrage': ArbitrageStrategy,
        'dca': DCAStrategy
    }
    
    if strategy_name.lower() not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies: {', '.join(strategies.keys())}")
    
    strategy_class = strategies[strategy_name.lower()]
    return strategy_class(strategy_name, params)

# Default parameters for each strategy
def get_default_params(strategy_name):
    """Get default parameters for a strategy"""
    params = {
        'scalping': {
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
        },
        'mean_reversion': {
            'lookback_period': 20,
            'entry_z_score': 2.0,
            'exit_z_score': 0.0,
            'stop_loss_percentage': 2.0,
            'take_profit_percentage': 4.0,
            'use_bollinger': True,
            'bollinger_std': 2.0
        },
        'trend_following': {
            'fast_ma_period': 9,
            'slow_ma_period': 21,
            'signal_ma_period': 9,
            'atr_period': 14,
            'stop_loss_atr_mult': 2.0,
            'trend_threshold': 0.02,
            'use_macd': True
        },
        'grid_trading': {
            'grid_levels': 10,
            'grid_size_pct': 1.0,
            'upper_limit_pct': 10.0,
            'lower_limit_pct': 10.0,
            'reference_price_type': 'current'
        },
        'arbitrage': {
            'min_profit_threshold': 0.15,
            'fee_percentage': 0.1,
            'slippage_percentage': 0.05,
            'position_timeout': 5
        },
        'dca': {
            'interval_hours': 24,
            'buy_amount': 100,
            'dip_threshold_pct': 5.0,
            'dip_multiplier': 1.5,
            'use_rsi': True,
            'rsi_oversold': 30
        }
    }
    
    return params.get(strategy_name.lower(), {})

def run_backtest(args):
    """
    Run backtest with specified parameters
    
    Parameters:
    -----------
    args : argparse.Namespace
        Command line arguments
    """
    # Setup logger
    logger = setup_logger('backtest', os.path.join('logs', 'backtest.log'))
    logger.info(f"Starting backtest with args: {args}")
    
    # Initialize history loader
    history_loader = HistoryLoader(logger)
    
    # Load historical data
    logger.info(f"Loading historical data for {args.symbol} from {args.start_date} to {args.end_date or 'now'}")
    df = history_loader.load_historical_data(
        symbol=args.symbol,
        interval=args.interval,
        start_str=args.start_date,
        end_str=args.end_date,
        use_mock=args.use_mock
    )
    
    if df is None or df.empty:
        logger.error("Failed to load historical data")
        return
        
    logger.info(f"Loaded {len(df)} candles of historical data")
    
    # Merge params if provided
    params = get_default_params(args.strategy)
    if args.params:
        try:
            custom_params = json.loads(args.params)
            params.update(custom_params)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON params: {args.params}")
    
    # Create strategy instance
    strategy = create_strategy(args.strategy, params)
    logger.info(f"Created {args.strategy} strategy with params: {params}")
    
    # Add required technical indicators
    df = strategy.calculate_indicators(df)
    
    # Create backtest engine
    engine = BacktestEngine(strategy, args.initial_capital, logger)
    
    # Run backtest
    logger.info("Running backtest...")
    results = engine.run(df)
    
    # Generate report
    report_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    report = engine.generate_report(report_path)
    print(report)
    
    # Plot results
    plot_path = os.path.join('data', 'plots', f"{args.symbol}_{args.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    engine.plot_results(plot_path, show_plot=args.show_plot)
    
    # Save results to JSON
    results_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    engine.save_results(results_path)
    
    logger.info(f"Backtest complete. Results saved to {results_path}")
    logger.info(f"Plot saved to {plot_path}")
    logger.info(f"Report saved to {report_path}")
    
    return results

def run_strategy_comparison(args):
    """
    Compare multiple strategies on the same dataset
    
    Parameters:
    -----------
    args : argparse.Namespace
        Command line arguments
    """
    # Setup logger
    logger = setup_logger('comparison', os.path.join('logs', 'comparison.log'))
    logger.info(f"Starting strategy comparison with args: {args}")
    
    # Initialize history loader
    history_loader = HistoryLoader(logger)
    
    # Load historical data
    logger.info(f"Loading historical data for {args.symbol} from {args.start_date} to {args.end_date or 'now'}")
    df = history_loader.load_historical_data(
        symbol=args.symbol,
        interval=args.interval,
        start_str=args.start_date,
        end_str=args.end_date,
        use_mock=args.use_mock
    )
    
    if df is None or df.empty:
        logger.error("Failed to load historical data")
        return
        
    logger.info(f"Loaded {len(df)} candles of historical data")
    
    # List of strategies to compare
    strategies = ['scalping', 'mean_reversion', 'trend_following', 'grid_trading', 'dca']
    
    if args.strategies:
        strategy_list = args.strategies.split(',')
        strategies = [s.strip().lower() for s in strategy_list if s.strip().lower() in strategies]
    
    results = {}
    
    # Run backtest for each strategy
    for strategy_name in strategies:
        logger.info(f"Running backtest for {strategy_name}...")
        
        # Get default params for this strategy
        params = get_default_params(strategy_name)
        
        # Create strategy instance
        strategy = create_strategy(strategy_name, params)
        
        # Add required technical indicators
        df_with_indicators = strategy.calculate_indicators(df)
        
        # Create backtest engine
        engine = BacktestEngine(strategy, args.initial_capital, logger)
        
        # Run backtest
        strategy_results = engine.run(df_with_indicators)
        
        # Save results
        results[strategy_name] = {
            'total_return': strategy_results['total_return'],
            'sharpe_ratio': strategy_results['sharpe_ratio'],
            'max_drawdown_pct': strategy_results['max_drawdown_pct'],
            'win_rate': strategy_results['win_rate'],
            'equity_curve': strategy_results['equity_curve'],
            'equity_timestamps': strategy_results['equity_timestamps']
        }
        
        # Generate individual report and plot
        report_path = os.path.join('data', 'results', f"{args.symbol}_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        engine.generate_report(report_path)
        
        plot_path = os.path.join('data', 'plots', f"{args.symbol}_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        engine.plot_results(plot_path, show_plot=False)
        
        logger.info(f"Completed backtest for {strategy_name}")
    
    # Create comparison plot
    comparison_path = os.path.join('data', 'plots', f"{args.symbol}_strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plot_strategy_comparison(results, comparison_path, args.symbol)
    
    # Print comparison table
    print("\nStrategy Comparison:")
    print("-" * 80)
    print(f"{'Strategy':<15} {'Return %':<10} {'Sharpe':<10} {'Drawdown %':<12} {'Win Rate %':<12}")
    print("-" * 80)
    
    for strategy_name, result in results.items():
        print(f"{strategy_name:<15} {result['total_return']:<10.2f} {result['sharpe_ratio']:<10.2f} {result['max_drawdown_pct']:<12.2f} {result['win_rate'] * 100:<12.2f}")
    
    print("-" * 80)
    
    # Save comparison results to JSON
    comparison_results_path = os.path.join('data', 'results', f"{args.symbol}_strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(comparison_results_path, 'w') as f:
        # Convert non-serializable data types
        serializable_results = {}
        for strategy_name, result in results.items():
            serializable_results[strategy_name] = {
                'total_return': float(result['total_return']),
                'sharpe_ratio': float(result['sharpe_ratio']),
                'max_drawdown_pct': float(result['max_drawdown_pct']),
                'win_rate': float(result['win_rate']),
            }
        
        json.dump(serializable_results, f, indent=4)
    
    logger.info(f"Comparison complete. Results saved to {comparison_results_path}")
    logger.info(f"Comparison plot saved to {comparison_path}")
    
    return results

def plot_strategy_comparison(results, filepath, symbol):
    """
    Create a comparison plot of multiple strategies
    
    Parameters:
    -----------
    results : dict
        Dictionary with results from each strategy
    filepath : str
        Path to save the plot
    symbol : str
        Symbol being traded
    """
    plt.figure(figsize=(14, 10))
    
    # Plot equity curves
    for strategy_name, result in results.items():
        # Normalize to percentage gain
        initial_value = result['equity_curve'][0]
        normalized_equity = [(v / initial_value - 1) * 100 for v in result['equity_curve']]
        
        # Convert timestamps if needed
        timestamps = []
        for ts in result['equity_timestamps']:
            if isinstance(ts, str):
                timestamps.append(pd.to_datetime(ts))
            else:
                timestamps.append(ts)
        
        plt.plot(timestamps, normalized_equity, label=strategy_name)
    
    plt.title(f"Strategy Comparison - {symbol}")
    plt.xlabel('Date')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

def run_parameter_optimization(args):
    """
    Optimize strategy parameters using grid search
    
    Parameters:
    -----------
    args : argparse.Namespace
        Command line arguments
    """
    # Setup logger
    logger = setup_logger('optimization', os.path.join('logs', 'optimization.log'))
    logger.info(f"Starting parameter optimization with args: {args}")
    
    # Initialize history loader
    history_loader = HistoryLoader(logger)
    
    # Load historical data
    logger.info(f"Loading historical data for {args.symbol} from {args.start_date} to {args.end_date or 'now'}")
    df = history_loader.load_historical_data(
        symbol=args.symbol,
        interval=args.interval,
        start_str=args.start_date,
        end_str=args.end_date,
        use_mock=args.use_mock
    )
    
    if df is None or df.empty:
        logger.error("Failed to load historical data")
        return
        
    logger.info(f"Loaded {len(df)} candles of historical data")
    
    # Parameter ranges for optimization
    param_ranges = get_optimization_ranges(args.strategy)
    
    if not param_ranges:
        logger.error(f"No optimization ranges defined for strategy: {args.strategy}")
        return
    
    # Generate parameter combinations
    param_combinations = []
    
    # If user provided params JSON, use it to override/limit the search space
    if args.params:
        try:
            user_params = json.loads(args.params)
            # Override param ranges with user-specified values
            for param, value in user_params.items():
                if param in param_ranges:
                    # If the value is a list, use it as the range
                    if isinstance(value, list):
                        param_ranges[param] = value
                    else:
                        # If it's a single value, use only that value
                        param_ranges[param] = [value]
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON params: {args.params}")
    
    # Generate combinations using grid search
    from itertools import product
    
    param_names = list(param_ranges.keys())
    param_values = [param_ranges[name] for name in param_names]
    
    for combo_values in product(*param_values):
        combo = {name: value for name, value in zip(param_names, combo_values)}
        param_combinations.append(combo)
    
    logger.info(f"Generated {len(param_combinations)} parameter combinations for testing")
    
    # Run backtest for each parameter combination
    results = []
    
    for i, params in enumerate(param_combinations):
        logger.info(f"Testing combination {i+1}/{len(param_combinations)}: {params}")
        
        # Create strategy with these parameters
        strategy = create_strategy(args.strategy, params)
        
        # Calculate indicators
        df_with_indicators = strategy.calculate_indicators(df)
        
        # Create backtest engine
        engine = BacktestEngine(strategy, args.initial_capital, logger)
        
        # Run backtest
        backtest_results = engine.run(df_with_indicators)
        
        # Store results
        results.append({
            'params': params,
            'total_return': backtest_results['total_return'],
            'sharpe_ratio': backtest_results['sharpe_ratio'],
            'max_drawdown_pct': backtest_results['max_drawdown_pct'],
            'win_rate': backtest_results['win_rate'],
            'profit_factor': backtest_results.get('profit_factor', 0)
        })
    
    # Sort results by metric
    sort_key = args.sort_by.lower() if args.sort_by else 'total_return'
    
    # For drawdown, lower is better
    reverse = sort_key != 'max_drawdown_pct'
    results.sort(key=lambda x: x[sort_key], reverse=reverse)
    
    # Write results to file
    results_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)
    
    # Print top results
    top_n = min(10, len(results))
    print(f"\nTop {top_n} parameter sets for {args.strategy} strategy:")
    print("-" * 100)
    
    headers = f"{'Rank':<5} {'Return %':<10} {'Sharpe':<10} {'Drawdown %':<12} {'Win Rate %':<12} {'Profit Factor':<15} Parameters"
    print(headers)
    print("-" * 100)
    
    for i in range(top_n):
        result = results[i]
        params_str = ', '.join([f"{k}={v}" for k, v in result['params'].items()])
        print(f"{i+1:<5} {result['total_return']:<10.2f} {result['sharpe_ratio']:<10.2f} "
              f"{result['max_drawdown_pct']:<12.2f} {result['win_rate'] * 100:<12.2f} "
              f"{result['profit_factor']:<15.2f} {params_str}")
    
    print("-" * 100)
    
    # Run backtest with best parameters
    best_params = results[0]['params']
    logger.info(f"Best parameters found: {best_params}")
    
    # Save best parameters to file
    best_params_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_best_params.json")
    with open(best_params_path, 'w') as f:
        json.dump(best_params, f, indent=4)
    
    # Create strategy with best parameters
    best_strategy = create_strategy(args.strategy, best_params)
    
    # Calculate indicators
    df_with_indicators = best_strategy.calculate_indicators(df)
    
    # Create backtest engine
    engine = BacktestEngine(best_strategy, args.initial_capital, logger)
    
    # Run backtest
    backtest_results = engine.run(df_with_indicators)
    
    # Generate report
    report_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    report = engine.generate_report(report_path)
    print("\nFinal backtest with best parameters:")
    print(report)
    
    # Plot results
    plot_path = os.path.join('data', 'plots', f"{args.symbol}_{args.strategy}_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    engine.plot_results(plot_path, show_plot=args.show_plot)
    
    logger.info(f"Optimization complete. Results saved to {results_path}")
    logger.info(f"Best parameters saved to {best_params_path}")
    logger.info(f"Plot saved to {plot_path}")
    
    return results

def get_optimization_ranges(strategy_name):
    """Get parameter ranges for strategy optimization"""
    ranges = {
        'scalping': {
            'ema_fast': [5, 8, 12],
            'ema_slow': [15, 21, 30],
            'rsi_period': [7, 14, 21],
            'rsi_oversold': [20, 30, 40],
            'rsi_overbought': [60, 70, 80],
            'bollinger_period': [10, 20, 30],
            'bollinger_std': [1.5, 2.0, 2.5],
            'stop_loss_percentage': [0.3, 0.5, 0.8, 1.0],
            'take_profit_percentage': [0.6, 1.0, 1.5, 2.0]
        },
        'mean_reversion': {
            'lookback_period': [10, 20, 30],
            'entry_z_score': [1.5, 2.0, 2.5],
            'exit_z_score': [0.0, 0.5, 1.0],
            'stop_loss_percentage': [1.0, 2.0, 3.0],
            'take_profit_percentage': [2.0, 3.0, 4.0, 5.0],
        },
        'trend_following': {
            'fast_ma_period': [5, 9, 13],
            'slow_ma_period': [15, 21, 30],
            'atr_period': [7, 14, 21],
            'stop_loss_atr_mult': [1.5, 2.0, 2.5, 3.0],
            'trend_threshold': [0.01, 0.02, 0.03]
        },
        'grid_trading': {
            'grid_levels': [5, 10, 15, 20],
            'grid_size_pct': [0.5, 1.0, 1.5],
            'upper_limit_pct': [5.0, 10.0, 15.0],
            'lower_limit_pct': [5.0, 10.0, 15.0]
        },
        'dca': {
            'interval_hours': [12, 24, 48],
            'dip_threshold_pct': [3.0, 5.0, 7.0],
            'dip_multiplier': [1.2, 1.5, 2.0],
            'rsi_oversold': [25, 30, 35]
        }
    }
    
    return ranges.get(strategy_name.lower(), {})

def run_walkforward_test(args):
    """
    Run walk-forward optimization and testing
    
    Parameters:
    -----------
    args : argparse.Namespace
        Command line arguments
    """
    # Setup logger
    logger = setup_logger('walkforward', os.path.join('logs', 'walkforward.log'))
    logger.info(f"Starting walk-forward testing with args: {args}")
    
    # Initialize history loader
    history_loader = HistoryLoader(logger)
    
    # Load historical data
    logger.info(f"Loading historical data for {args.symbol} from {args.start_date} to {args.end_date or 'now'}")
    df = history_loader.load_historical_data(
        symbol=args.symbol,
        interval=args.interval,
        start_str=args.start_date,
        end_str=args.end_date,
        use_mock=args.use_mock
    )
    
    if df is None or df.empty:
        logger.error("Failed to load historical data")
        return
        
    logger.info(f"Loaded {len(df)} candles of historical data")
    
    # Get parameter ranges for the strategy
    param_ranges = get_optimization_ranges(args.strategy)
    
    if not param_ranges:
        logger.error(f"No optimization ranges defined for strategy: {args.strategy}")
        return
    
    # Generate parameter combinations for testing
    param_combinations = []
    
    # Generate combinations using grid search
    from itertools import product
    
    param_names = list(param_ranges.keys())
    param_values = [param_ranges[name] for name in param_names]
    
    for combo_values in product(*param_values):
        combo = {name: value for name, value in zip(param_names, combo_values)}
        param_combinations.append(combo)
    
    logger.info(f"Generated {len(param_combinations)} parameter combinations for testing")
    
    # Get the strategy class
    strategy_classes = {
        'scalping': ScalpingStrategy,
        'mean_reversion': MeanReversionStrategy,
        'trend_following': TrendFollowingStrategy,
        'grid_trading': GridTradingStrategy,
        'arbitrage': ArbitrageStrategy,
        'dca': DCAStrategy
    }
    
    strategy_class = strategy_classes.get(args.strategy.lower())
    
    if not strategy_class:
        logger.error(f"Unknown strategy: {args.strategy}")
        return
    
    # Run walk-forward optimization
    logger.info("Running walk-forward optimization...")
    
    # Set window sizes for walk-forward test
    window_size = int(len(df) * 0.6)  # 60% of data for training
    validation_size = int(len(df) * 0.2)  # 20% of data for validation
    step_size = validation_size  # Move forward by validation window size
    
    if args.window_size:
        window_size = int(args.window_size)
    if args.validation_size:
        validation_size = int(args.validation_size)
    if args.step_size:
        step_size = int(args.step_size)
    
    # Run walk-forward optimization
    wf_results = run_walk_forward(
        strategy_class=strategy_class,
        data=df,
        params_list=param_combinations,
        initial_capital=args.initial_capital,
        window_size=window_size,
        step_size=step_size,
        validation_size=validation_size,
        logger=logger
    )
    
    if not wf_results:
        logger.error("Walk-forward optimization failed")
        return
    
    # Process results
    logger.info(f"Walk-forward optimization complete. {wf_results['windows']} windows analyzed.")
    
    # Calculate average validation performance
    validation_returns = [r['validation_return'] for r in wf_results['results']]
    avg_validation_return = np.mean(validation_returns)
    
    logger.info(f"Average validation return: {avg_validation_return:.2f}%")
    
    # Find most stable parameters
    param_stability = wf_results['params_stability']
    
    # Print stability analysis
    print("\nParameter Stability Analysis:")
    print("-" * 80)
    for param, stats in param_stability.items():
        print(f"{param}:")
        print(f"  Mean: {stats['mean']:.4f}")
        print(f"  Median: {stats['median']:.4f}")
        print(f"  Std Dev: {stats['std']:.4f}")
        print(f"  Min: {stats['min']:.4f}")
        print(f"  Max: {stats['max']:.4f}")
        print(f"  Stability: {stats['stability']:.4f}")
        print()
    
    # Generate report
    report_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_walkforward_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(report_path, 'w') as f:
        f.write(f"Walk-Forward Optimization Results - {args.symbol} {args.strategy}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Parameters:\n")
        f.write(f"  Window Size: {window_size}\n")
        f.write(f"  Validation Size: {validation_size}\n")
        f.write(f"  Step Size: {step_size}\n")
        f.write(f"  Windows: {wf_results['windows']}\n\n")
        
        f.write("Overall Performance:\n")
        f.write(f"  Average Validation Return: {avg_validation_return:.2f}%\n\n")
        
        f.write("Window Results:\n")
        for i, result in enumerate(wf_results['results']):
            f.write(f"  Window {i+1}:\n")
            f.write(f"    Train Period: {result['train_start']} to {result['train_end']}\n")
            f.write(f"    Valid Period: {result['valid_start']} to {result['valid_end']}\n")
            f.write(f"    Train Return: {result['train_return']:.2f}%\n")
            f.write(f"    Valid Return: {result['validation_return']:.2f}%\n")
            f.write(f"    Best Params: {result['best_params']}\n\n")
    
    # Save results to JSON
    results_path = os.path.join('data', 'results', f"{args.symbol}_{args.strategy}_walkforward_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(results_path, 'w') as f:
        # Make results JSON serializable
        serializable_results = {}
        for key, value in wf_results.items():
            if key == 'results':
                serializable_results[key] = []
                for result in value:
                    serializable_results[key].append({
                        'window': result['window'],
                        'train_start': str(result['train_start']),
                        'train_end': str(result['train_end']),
                        'valid_start': str(result['valid_start']),
                        'valid_end': str(result['valid_end']),
                        'best_params': result['best_params'],
                        'train_return': float(result['train_return']),
                        'validation_return': float(result['validation_return'])
                    })
            elif key == 'best_params_over_time':
                serializable_results[key] = value
            elif key == 'params_stability':
                serializable_results[key] = {}
                for param, stats in value.items():
                    serializable_results[key][param] = {
                        stat_key: float(stat_value) for stat_key, stat_value in stats.items()
                    }
            else:
                serializable_results[key] = value
        
        json.dump(serializable_results, f, indent=4)
    
    # Plot validation returns across windows
    plot_path = os.path.join('data', 'plots', f"{args.symbol}_{args.strategy}_walkforward_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    
    plt.figure(figsize=(12, 8))
    
    # Plot training and validation returns
    windows = list(range(1, len(validation_returns) + 1))
    training_returns = [r['train_return'] for r in wf_results['results']]
    
    plt.plot(windows, training_returns, 'b-', label='Training Return')
    plt.plot(windows, validation_returns, 'g-', label='Validation Return')
    
    plt.axhline(y=0, color='r', linestyle='--')
    plt.axhline(y=avg_validation_return, color='g', linestyle='--', label=f'Avg Validation: {avg_validation_return:.2f}%')
    
    plt.title(f"Walk-Forward Testing Results - {args.symbol} {args.strategy}")
    plt.xlabel('Window')
    plt.ylabel('Return (%)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    
    if args.show_plot:
        plt.show()
    else:
        plt.close()
    
    logger.info(f"Walk-forward testing complete. Results saved to {results_path}")
    logger.info(f"Report saved to {report_path}")
    logger.info(f"Plot saved to {plot_path}")
    
    print(f"\nWalk-forward testing complete.")
    print(f"Average validation return: {avg_validation_return:.2f}%")
    print(f"Results saved to {results_path}")
    print(f"Plot saved to {plot_path}")
    
    return wf_results

def main():
    """Main function for command line execution"""
    parser = argparse.ArgumentParser(description='Advanced Cryptocurrency Trading Bot Backtester')
    
    # Required arguments
    parser.add_argument('--symbol', type=str, required=True, help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('--start-date', type=str, required=True, help='Start date for backtesting')
    
    # Optional arguments
    parser.add_argument('--end-date', type=str, help='End date for backtesting (default: now)')
    parser.add_argument('--interval', type=str, default='1h', help='Candlestick interval (e.g., 1m, 5m, 1h, 1d)')
    parser.add_argument('--strategy', type=str, default='scalping', 
                       help='Trading strategy to backtest (scalping, mean_reversion, trend_following, grid_trading, arbitrage, dca)')
    parser.add_argument('--initial-capital', type=float, default=1000.0, help='Initial capital for backtesting')
    parser.add_argument('--params', type=str, help='JSON string of strategy parameters')
    parser.add_argument('--use-mock', action='store_true', help='Use mock data for testing')
    parser.add_argument('--show-plot', action='store_true', help='Show plots during execution')
    
    # Mode selection
    parser.add_argument('--mode', type=str, default='backtest', 
                       help='Mode: backtest, compare, optimize, walkforward')
    
    # Comparison mode arguments
    parser.add_argument('--strategies', type=str, help='Comma-separated list of strategies to compare')
    
    # Optimization mode arguments
    parser.add_argument('--sort-by', type=str, default='total_return', 
                       help='Metric to sort optimization results by: total_return, sharpe_ratio, max_drawdown_pct, win_rate')
    
    # Walk-forward mode arguments
    parser.add_argument('--window-size', type=int, help='Training window size for walk-forward testing')
    parser.add_argument('--validation-size', type=int, help='Validation window size for walk-forward testing')
    parser.add_argument('--step-size', type=int, help='Step size for walk-forward windows')
    
    args = parser.parse_args()
    
    # Create necessary directories
    ensure_directories()
    
    # Execute the appropriate mode
    if args.mode.lower() == 'backtest':
        run_backtest(args)
    elif args.mode.lower() == 'compare':
        run_strategy_comparison(args)
    elif args.mode.lower() == 'optimize':
        run_parameter_optimization(args)
    elif args.mode.lower() == 'walkforward':
        run_walkforward_test(args)
    else:
        print(f"Unknown mode: {args.mode}")
        parser.print_help()

if __name__ == '__main__':
    main()
