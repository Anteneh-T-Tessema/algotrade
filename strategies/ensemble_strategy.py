#!/usr/bin/env python3
"""
Starter implementation of an Ensemble Strategy that combines multiple sub-strategies
based on predefined weights per market condition.
"""
from typing import Dict, Type
import os
import json
from strategies.base_strategy import Strategy

class EnsembleStrategy(Strategy):
    """
    An ensemble of multiple strategy classes, weighting their signals
    according to the current market type.
    """
    def __init__(self,
                 name: str,
                 params: Dict = None,
                 strategy_classes: Dict[str, Type[Strategy]] = None,
                 weight_table: Dict[str, Dict[str, float]] = None):
        """
        :param name: Ensemble name
        :param params: global parameters (should include 'market_type')
        :param strategy_classes: mapping of sub-strategy names to their classes
        :param weight_table: mapping of market_type -> {strategy_name: weight}
        """
        super().__init__(name, params)
        self.strategy_instances = {}
        for strat_name, strat_cls in (strategy_classes or {}).items():
            # instantiate each sub-strategy with same params or separate per strategy
            self.strategy_instances[strat_name] = strat_cls(strat_name, params)

        self.weight_table = weight_table or {}

    @staticmethod
    def load_weight_table_from_file(file_path=None):
        """
        Utility method to load weight table from the JSON file
        
        :param file_path: Path to weight table JSON file (optional)
        :return: Dictionary mapping market types to strategy weights
        """
        if file_path is None:
            # Default weight table path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, 'data', 'weight_table.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            weight_table = json.load(f)
        return weight_table

    def calculate_indicators(self, df):
        # Allow each sub-strategy to compute its own indicators
        out = df.copy()
        for strat in self.strategy_instances.values():
            out = strat.calculate_indicators(out)
        return out

    def generate_signal(self, df):
        # Determine market type for weighting
        market_type = self.params.get('market_type')
        weights = self.weight_table.get(market_type, {})

        # Aggregate weighted signals from each sub-strategy
        score = 0.0
        for name, strat in self.strategy_instances.items():
            raw_signal = strat.generate_signal(df)
            # Map signal to numeric
            val = {'BUY': 1.0, 'SELL': -1.0}.get(raw_signal, 0.0)
            w = weights.get(name, 0.0)
            score += w * val

        # Interpret aggregate score
        threshold = self.params.get('ensemble_threshold', 0.5)
        if score > threshold:
            return 'BUY'
        elif score < -threshold:
            return 'SELL'
        else:
            return 'HOLD'

    # Optional override of on_candle if you need to handle multiple sub-strategy orders
    # def on_candle(self, candle, balance):
    #     ...


# Example of how to set up weights for different market regimes:
# WEIGHT_TABLE = {
#     'trending': {'TrendFollowing': 0.7, 'MeanReversion': 0.1, 'Scalping': 0.2},
#     'volatile': {'MeanReversion': 0.5, 'GridTrading': 0.5},
#     'sideways': {'GridTrading': 0.6, 'Scalping': 0.4},
#     'normal':   {'TrendFollowing': 0.4, 'MeanReversion': 0.3, 'Scalping': 0.3},
# }
