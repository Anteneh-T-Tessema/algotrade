#!/usr/bin/env python3
"""
Demo script showing how to use the EnsembleStrategy with dynamic weights
"""
import importlib
import os
import sys
import logging

# Ensure the project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from strategies.ensemble_strategy import EnsembleStrategy
from strategies.trend_following_strategy import TrendFollowingStrategy
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.scalping_strategy import ScalpingStrategy
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.dca_strategy import DCAStrategy
from strategies.arbitrage_strategy import ArbitrageStrategy

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    logger = logging.getLogger("ensemble_demo")
    
    # Load the weight table from file
    try:
        logger.info("Attempting to load weight table...")
        weight_table = EnsembleStrategy.load_weight_table_from_file()
        logger.info(f"Loaded weight table with {len(weight_table)} market types")
        for market_type, weights in weight_table.items():
            logger.info(f"Market type: {market_type} has {len(weights)} strategy weights")
    except Exception as e:
        logger.error(f"Failed to load weight table: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    # Create a dictionary of strategy classes
    strategy_classes = {
        'TrendFollowing': TrendFollowingStrategy,
        'MeanReversion': MeanReversionStrategy,
        'Scalping': ScalpingStrategy,
        'GridTrading': GridTradingStrategy,
        'DCA': DCAStrategy,
        'Arbitrage': ArbitrageStrategy
    }
    
    # Set parameters for testing - you can change the market_type to see how
    # weights and signals change
    params = {
        'market_type': 'trending market',  # Change this to test different market types
        'ensemble_threshold': 0.3,
        'other_param': 'value'
    }
    
    # Create the ensemble strategy
    ensemble = EnsembleStrategy(
        name="DynamicEnsemble",
        params=params,
        strategy_classes=strategy_classes,
        weight_table=weight_table
    )
    
    # Display weights for current market type
    market_type = params['market_type']
    weights = weight_table.get(market_type, {})
    logger.info(f"Weights for {market_type}:")
    for strat_name, weight in weights.items():
        if weight > 0:
            logger.info(f"  {strat_name}: {weight:.4f}")
    
    logger.info("Ensemble strategy setup complete!")
    logger.info("In a real application, you would now feed candle data to the strategy")
    logger.info("and process the generated signals.")

if __name__ == "__main__":
    main()
