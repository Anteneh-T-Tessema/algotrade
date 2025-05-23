#!/usr/bin/env python3
"""
Deployment Script for Trading Bot

This script helps deploy the trading bot with the most effective strategy
based on backtesting results. It analyzes previous backtest results,
selects the best strategy for the current market conditions, and launches
the trading bot with the optimal configuration.
"""

import os
import sys
import argparse
import json
import logging
import pandas as pd
import numpy as np
import traceback
from datetime import datetime, timedelta
import yaml

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities
from utils.logger import setup_logger
from utils.history_loader import HistoryLoader

# Set up directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'data', 'results')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

def setup_logger_for_deployment():
    """Set up logger for deployment"""
    log_dir = os.path.join(BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return setup_logger('deploy', os.path.join(log_dir, 'deploy.log'))

def load_recent_backtest_results():
    """Load the most recent backtest results for each strategy"""
    logger = logging.getLogger('deploy')
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    result_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')]
    
    if not result_files:
        logger.warning("No backtest results found. Run backtests before deploying.")
        return None
    
    # Group result files by strategy
    strategy_results = {}
    
    for file in result_files:
        try:
            with open(os.path.join(RESULTS_DIR, file), 'r') as f:
                result = json.load(f)
                strategy_name = result.get('strategy', 'unknown')
                
                if strategy_name not in strategy_results:
                    strategy_results[strategy_name] = []
                    
                # Add file timestamp
                file_timestamp = file.split('_')[-1].replace('.json', '')
                try:
                    timestamp = datetime.strptime(file_timestamp, '%Y%m%d%H%M%S')
                except ValueError:
                    timestamp = datetime.now() - timedelta(days=1)  # Default if can't parse
                    
                result['timestamp'] = timestamp
                strategy_results[strategy_name].append(result)
        except Exception as e:
            logger.error(f"Error loading {file}: {str(e)}")
    
    # Get the most recent result for each strategy
    recent_results = {}
    for strategy, results in strategy_results.items():
        # Sort by timestamp
        recent_result = sorted(results, key=lambda x: x.get('timestamp', datetime.min))[-1]
        recent_results[strategy] = recent_result
    
    return recent_results

def analyze_market_conditions(symbol='BTCUSDT', timeframe='1d', lookback_days=30):
    """
    Analyze current market conditions to determine the market type.
    
    Parameters:
    -----------
    symbol : str
        Symbol to analyze
    timeframe : str
        Timeframe for analysis ('1h', '4h', '1d', etc.)
    lookback_days : int
        Number of days to look back for analysis
        
    Returns:
    --------
    dict
        Dictionary with market condition analysis results
        {
            'market_type': str ('trending', 'ranging', 'volatile', etc.),
            'trend_direction': str ('up', 'down', 'neutral'),
            'volatility': float (volatility measurement),
            'momentum': float (momentum measurement),
            'recommendation': str (recommended strategy type)
        }
    """
    logger = logging.getLogger('deploy')
    logger.info(f"Analyzing market conditions for {symbol} on {timeframe} timeframe")
    
    try:
        # Load historical data
        history_loader = HistoryLoader()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get historical data
        df = history_loader.load_history(symbol, timeframe, start_date, end_date)
        
        if df is None or len(df) < 10:
            logger.warning(f"Insufficient data for {symbol} on {timeframe} timeframe")
            return {'market_type': 'unknown', 'recommendation': 'trend_following'}
        
        # Calculate technical indicators
        # 1. Volatility (ATR relative to price)
        df['tr1'] = abs(df['high'] - df['low'])
        df['tr2'] = abs(df['high'] - df['close'].shift())
        df['tr3'] = abs(df['low'] - df['close'].shift())
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr14'] = df['true_range'].rolling(window=14).mean()
        df['volatility'] = df['atr14'] / df['close'] * 100  # ATR as percentage of price
        
        current_volatility = df['volatility'].iloc[-1]
        
        # 2. Trend (using moving averages)
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        
        # Determine if price is trending based on SMA relationship
        trending_up = df['sma20'].iloc[-1] > df['sma50'].iloc[-1] and df['close'].iloc[-1] > df['sma20'].iloc[-1]
        trending_down = df['sma20'].iloc[-1] < df['sma50'].iloc[-1] and df['close'].iloc[-1] < df['sma20'].iloc[-1]
        
        # 3. Range analysis (check if price is respecting horizontal levels)
        last_n = min(30, len(df))
        price_range = (df['high'].iloc[-last_n:].max() - df['low'].iloc[-last_n:].min()) / df['low'].iloc[-last_n:].min() * 100
        
        # 4. Momentum (using ROC - Rate of Change)
        df['roc10'] = (df['close'] / df['close'].shift(10) - 1) * 100
        current_momentum = df['roc10'].iloc[-1]
        
        # Classify market type
        is_volatile = current_volatility > 3.0  # 3% is considered high volatility
        is_ranging = price_range < 15.0 and not (trending_up or trending_down)  # Less than 15% range and no clear trend
        is_trending = trending_up or trending_down
        
        # Determine market type and recommended strategy
        if is_volatile:
            market_type = 'volatile'
            recommendation = 'grid_trading' if is_ranging else 'mean_reversion'
        elif is_trending:
            market_type = 'trending'
            trend_direction = 'up' if trending_up else 'down'
            recommendation = 'trend_following'
        elif is_ranging:
            market_type = 'ranging'
            recommendation = 'grid_trading'
        else:
            market_type = 'normal'
            recommendation = 'scalping'
        
        # Compile results
        results = {
            'market_type': market_type,
            'trend_direction': 'up' if trending_up else ('down' if trending_down else 'neutral'),
            'volatility': current_volatility,
            'momentum': current_momentum,
            'price_range_pct': price_range,
            'recommendation': recommendation
        }
        
        logger.info(f"Market analysis results: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing market conditions: {str(e)}")
        logger.debug(traceback.format_exc())
        return {'market_type': 'unknown', 'recommendation': 'trend_following'}

def select_best_strategy(backtest_results, market_type=None):
    """Select the best strategy based on backtest results and market conditions"""
    logger = logging.getLogger('deploy')
    
    if not backtest_results:
        logger.warning("No backtest results available. Defaulting to trend_following strategy.")
        return "trend_following"
    
    # If market type is provided, use that to help select the strategy
    if market_type:
        # Filter relevant strategies for this market type
        if market_type == "trending":
            candidates = ["trend_following", "dca"]
        elif market_type == "ranging":
            candidates = ["grid_trading", "mean_reversion"]
        elif market_type == "volatile":
            candidates = ["mean_reversion", "scalping"]
        else:
            candidates = list(backtest_results.keys())
        
        # Filter by available backtest results
        candidates = [s for s in candidates if s in backtest_results]
        
        if not candidates:
            # If no matching candidates, fall back to all strategies
            candidates = list(backtest_results.keys())
    else:
        candidates = list(backtest_results.keys())
    
    # Create a scoring system for strategies (considering multiple factors)
    strategy_scores = {}
    
    for strategy_name in candidates:
        result = backtest_results.get(strategy_name)
        if not result:
            continue
            
        # Extract metrics
        # We'll use a weighted score of several metrics:
        # - Sharpe ratio (risk-adjusted returns)
        # - Total return
        # - Max drawdown (negative factor)
        # - Win rate
        
        sharpe = result.get('sharpe_ratio', 0)
        returns = result.get('total_return', 0)
        drawdown = result.get('max_drawdown_pct', 100)
        win_rate = result.get('win_rate', 0)
        
        # Calculate score with weights
        score = (
            0.4 * sharpe +
            0.3 * (returns / 100) +
            0.2 * (1 - drawdown / 100) +  # Convert drawdown to positive score
            0.1 * win_rate
        )
        
        strategy_scores[strategy_name] = score
    
    if not strategy_scores:
        logger.warning("No valid strategy scores computed. Defaulting to trend_following.")
        return "trend_following"
    
    # Select strategy with highest score
    best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
    logger.info(f"Strategy scores: {strategy_scores}")
    logger.info(f"Selected best strategy: {best_strategy[0]} (score: {best_strategy[1]:.4f})")
    
    return best_strategy[0]

def get_strategy_params(strategy_name):
    """Get the best parameters for the selected strategy"""
    logger = logging.getLogger('deploy')
    
    # Check for optimized params in backtest results
    for file in os.listdir(RESULTS_DIR):
        if strategy_name in file and file.endswith('.json'):
            try:
                with open(os.path.join(RESULTS_DIR, file), 'r') as f:
                    result = json.load(f)
                    if 'strategy_params' in result:
                        return result['strategy_params']
            except Exception as e:
                logger.error(f"Error loading parameters from {file}: {str(e)}")
    
    # Fall back to default parameters
    from advanced_backtest import get_default_params
    return get_default_params(strategy_name)

def update_config(strategy_name, params):
    """Update the config.yaml file with the selected strategy and parameters"""
    logger = logging.getLogger('deploy')
    
    config_file = os.path.join(CONFIG_DIR, 'config.yaml')
    
    try:
        # Load current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update strategy settings
        config['strategy_type'] = strategy_name
        config['strategy'] = params
        
        # Save updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        logger.info(f"Config updated with {strategy_name} strategy and parameters")
        
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return False
        
    return True

def deploy_bot(strategy_name=None, params=None, test_mode=True):
    """
    Deploy the trading bot with the selected strategy
    
    Parameters
    ----------
    strategy_name : str, optional
        Name of the strategy to deploy. If None, the best strategy will be selected
        based on current market conditions and backtest results
    params : dict, optional
        Strategy parameters. If None, optimal parameters will be loaded
    test_mode : bool
        Whether to run in test mode (True) or live trading mode (False)
    
    Returns
    -------
    bool
        True if deployment was successful, False otherwise
    """
    logger = logging.getLogger('deploy')
    
    try:
        if not strategy_name:
            # Determine current market conditions
            symbol = "BTCUSDT"  # Default to BTC, could make this configurable
            logger.info(f"Analyzing current market conditions for {symbol}...")
            market_type = analyze_market_conditions(symbol)
            
            # Load backtest results
            logger.info("Loading recent backtest results...")
            backtest_results = load_recent_backtest_results()
            
            # Select best strategy based on market conditions and backtest performance
            if not backtest_results:
                logger.warning("No backtest results available. Defaulting to trend_following strategy")
                strategy_name = "trend_following"
            else:
                logger.info(f"Selecting best strategy for {market_type} market conditions...")
                strategy_name = select_best_strategy(backtest_results, market_type)
        
        logger.info(f"Selected strategy: {strategy_name}")
        
        if not params:
            # Get optimized parameters for the strategy
            logger.info(f"Loading optimal parameters for {strategy_name} strategy...")
            params = get_strategy_params(strategy_name)
            if not params:
                logger.warning(f"No optimized parameters found for {strategy_name}. Using defaults.")
        
        # Update configuration file
        logger.info("Updating configuration...")
        update_config(strategy_name, params)
        
        # Safety check
        if not test_mode:
            logger.warning("Preparing to deploy in LIVE trading mode!")
            
            # Update config to use live settings
            with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'r') as f:
                config = yaml.safe_load(f)
                config['exchange']['testnet'] = False
                
            with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            logger.warning("Configuration updated for LIVE trading")
        else:
            logger.info("Deploying in TEST mode (using testnet)")
            
            # Ensure testnet is enabled in config
            with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'r') as f:
                config = yaml.safe_load(f)
                config['exchange']['testnet'] = True
                
            with open(os.path.join(CONFIG_DIR, 'config.yaml'), 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        
        # Launch the trading bot
        logger.info(f"Deploying trading bot with {strategy_name} strategy")
        
        try:
            # Import and run the bot
            from bot import TradingBot
            bot = TradingBot()
            bot.start()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped manually by user")
            return True
            
        except Exception as e:
            logger.error(f"Error running trading bot: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
        return True
    
    except Exception as e:
        logger.error(f"Error during deployment process: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the deployment script"""
    parser = argparse.ArgumentParser(description='Deploy trading bot with optimal strategy')
    parser.add_argument('--strategy', help='Force a specific strategy', default=None)
    parser.add_argument('--live', action='store_true', help='Enable live trading (default: test mode)')
    parser.add_argument('--analyze', action='store_true', help='Only analyze market and recommend strategy without deployment')
    parser.add_argument('--test-strategies', action='store_true', help='Run strategy tests before deployment')
    parser.add_argument('--symbol', default='BTCUSDT', help='Symbol to analyze for market conditions')
    args = parser.parse_args()
    
    logger = setup_logger_for_deployment()
    logger.info("Starting deployment process")
    
    # Run strategy tests if requested
    if args.test_strategies:
        logger.info("Running strategy tests before deployment...")
        try:
            import test_all_strategies
            results = test_all_strategies.test_all_strategies()
            logger.info("Strategy testing completed")
        except Exception as e:
            logger.error(f"Error running strategy tests: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Only analyze market conditions if requested
    if args.analyze:
        market_type = analyze_market_conditions(args.symbol)
        backtest_results = load_recent_backtest_results()
        best_strategy = select_best_strategy(backtest_results, market_type)
        
        logger.info(f"Market analysis for {args.symbol}:")
        logger.info(f"- Market type: {market_type}")
        logger.info(f"- Recommended strategy: {best_strategy}")
        
        if backtest_results and best_strategy in backtest_results:
            result = backtest_results[best_strategy]
            logger.info(f"- Expected performance (based on backtests):")
            logger.info(f"  - Total return: {result.get('total_return', 'N/A'):.2f}%")
            logger.info(f"  - Win rate: {result.get('win_rate', 'N/A')*100:.2f}%")
            logger.info(f"  - Sharpe ratio: {result.get('sharpe_ratio', 'N/A'):.2f}")
        return
    
    # Deploy bot with specified options
    if args.strategy:
        logger.info(f"Forcing deployment with {args.strategy} strategy")
        deploy_bot(strategy_name=args.strategy, test_mode=not args.live)
    else:
        logger.info(f"Deploying bot with best strategy for current market conditions")
        deploy_bot(test_mode=not args.live)
        
if __name__ == "__main__":
    main()
