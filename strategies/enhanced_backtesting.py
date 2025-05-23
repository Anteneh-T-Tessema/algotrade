"""
Enhanced Backtesting Module

This module provides enhanced backtesting functionality for trading strategies.
It focuses on:
1. Monthly performance breakdown
2. Win/loss streak tracking
3. Market condition analysis
4. Exit reason analysis
5. Risk metrics calculation
"""

import numpy as np
import pandas as pd
import logging
import traceback
from typing import Dict, List, Any, Tuple, Optional, Union

class BacktestEnhancer:
    """
    Enhances backtesting capabilities for trading strategies with comprehensive metrics
    and detailed performance analysis across different market conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhancer with optional configuration."""
        self.config = config or {}

    @staticmethod
    def calculate_performance_metrics(
        trades: List[Dict[str, Any]], 
        equity_curve: List[float], 
        initial_balance: float, 
        daily_returns: Dict[Any, Dict[str, float]],
        monthly_returns: Dict[str, Dict[str, Any]],
        volatility_trades: Dict[str, Dict[str, Any]],
        correlation_trades: Dict[str, Dict[str, Any]],
        max_drawdown: float,
        max_drawdown_duration: int
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics from backtest results.
        
        Parameters:
        -----------
        trades : list
            List of trade dictionaries, each containing details of a trade
        equity_curve : list
            List of account balances over time
        initial_balance : float
            Starting account balance
        daily_returns : dict
            Daily account balance changes
        monthly_returns : dict
            Monthly account balance changes
        volatility_trades : dict
            Performance metrics grouped by volatility level
        correlation_trades : dict
            Performance metrics grouped by market correlation/bias
        max_drawdown : float
            Maximum drawdown percentage
        max_drawdown_duration : int
            Maximum drawdown duration in candles/periods
            
        Returns:
        --------
        dict
            Comprehensive performance metrics dictionary
        """
        if not trades:
            return {'error': 'No trades executed'}
        
        # Basic trade metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # Profit metrics
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = sum(t.get('pnl', 0) for t in losing_trades)
        net_profit = gross_profit + gross_loss
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        avg_profit = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Return metrics
        final_balance = equity_curve[-1] if equity_curve else initial_balance
        final_return_pct = (final_balance - initial_balance) / initial_balance * 100
        
        # Calculate expectancy
        avg_win_pct = sum(t.get('pnl_percentage', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss_pct = sum(t.get('pnl_percentage', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
        win_probability = win_rate / 100
        expectancy = (win_probability * avg_win_pct) - ((1 - win_probability) * abs(avg_loss_pct))
        
        # Calculate Sharpe ratio from daily returns
        sharpe_ratio = BacktestEnhancer._calculate_sharpe_ratio(daily_returns)
        
        # Calculate Sortino ratio (using only negative returns for denominator)
        sortino_ratio = BacktestEnhancer._calculate_sortino_ratio(daily_returns)
        
        # Monthly return analysis
        monthly_performance = {}
        for month, values in monthly_returns.items():
            if values.get('start_balance', 0) > 0:
                monthly_performance[month] = {
                    'return_pct': (values.get('end_balance', 0) - values.get('start_balance', 0)) / values.get('start_balance', 1) * 100,
                    'trades': values.get('trades', 0),
                    'win_rate': (values.get('profitable_trades', 0) / values.get('trades', 1) * 100) if values.get('trades', 0) > 0 else 0
                }
        
        # Trade duration metrics
        durations = [t.get('duration', 0) for t in trades]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Win/loss streak analysis
        win_loss_streaks = BacktestEnhancer._calculate_win_loss_streaks(trades)
        
        # Analyze exit reasons
        exit_reasons = BacktestEnhancer._analyze_exit_reasons(trades)
        
        # Calculate win rate for different market correlations and volatility levels
        for bias in correlation_trades:
            if correlation_trades[bias]['count'] > 0:
                correlation_trades[bias]['win_rate'] = (correlation_trades[bias]['wins'] / correlation_trades[bias]['count']) * 100
                correlation_trades[bias]['avg_pnl'] = correlation_trades[bias]['pnl'] / correlation_trades[bias]['count']
        
        for vol in volatility_trades:
            if volatility_trades[vol]['count'] > 0:
                volatility_trades[vol]['win_rate'] = (volatility_trades[vol]['wins'] / volatility_trades[vol]['count']) * 100
                volatility_trades[vol]['avg_pnl'] = volatility_trades[vol]['pnl'] / volatility_trades[vol]['count']
        
        # Prepare comprehensive result dictionary
        results = {
            # Basic trade metrics
            'total_trades': total_trades,
            'win_rate': win_rate,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            
            # Profit metrics
            'net_profit': net_profit,
            'net_profit_percent': final_return_pct,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': abs(avg_loss_pct),
            'expectancy': expectancy,
            'expected_value': expectancy / 100 * initial_balance,  # Expected $ value per trade
            
            # Risk metrics
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_drawdown_duration,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            
            # Trade duration metrics
            'trade_durations': {
                'avg': avg_duration,
                'min': min_duration,
                'max': max_duration
            },
            
            # Trade streaks
            'max_consecutive_wins': win_loss_streaks['max_consecutive_wins'],
            'max_consecutive_losses': win_loss_streaks['max_consecutive_losses'],
            
            # Detailed analysis
            'monthly_performance': monthly_performance,
            'exit_reason_analysis': exit_reasons,
            'market_correlation_analysis': correlation_trades,
            'volatility_analysis': volatility_trades,
            
            # Final results
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'return_percent': final_return_pct,
            'annual_return': final_return_pct * (252 / len(daily_returns)) if daily_returns else "N/A"
        }
        
        return results
    
    @staticmethod
    def _calculate_sharpe_ratio(daily_returns: Dict[Any, Dict[str, float]]) -> float:
        """Calculate annualized Sharpe ratio from daily returns"""
        if not daily_returns:
            return 0
            
        daily_return_values = []
        for date, values in daily_returns.items():
            if values.get('start_balance', 0) > 0:
                daily_pct_return = (values.get('end_balance', 0) - values.get('start_balance', 0)) / values.get('start_balance', 1) * 100
                daily_return_values.append(daily_pct_return)
        
        # Calculate annualized Sharpe ratio if we have enough data
        if len(daily_return_values) > 1:
            mean_return = np.mean(daily_return_values)
            std_return = np.std(daily_return_values)
            if std_return > 0:
                # Convert to annualized Sharpe ratio (√252 is standard for daily)
                risk_free_rate = 0  # Assuming 0% risk-free rate
                sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
                return sharpe_ratio
                
        return 0
    
    @staticmethod
    def _calculate_sortino_ratio(daily_returns: Dict[Any, Dict[str, float]]) -> float:
        """Calculate annualized Sortino ratio from daily returns"""
        if not daily_returns:
            return 0
            
        daily_return_values = []
        for date, values in daily_returns.items():
            if values.get('start_balance', 0) > 0:
                daily_pct_return = (values.get('end_balance', 0) - values.get('start_balance', 0)) / values.get('start_balance', 1) * 100
                daily_return_values.append(daily_pct_return)
        
        # Calculate Sortino ratio 
        if daily_return_values:
            negative_returns = [ret for ret in daily_return_values if ret < 0]
            if negative_returns:
                mean_return = np.mean(daily_return_values)
                downside_deviation = np.std(negative_returns)
                if downside_deviation > 0:
                    sortino_ratio = (mean_return - 0) / downside_deviation * np.sqrt(252)  # Annualized
                    return sortino_ratio
                    
        return 0
    
    @staticmethod
    def _calculate_win_loss_streaks(trades: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate maximum consecutive wins and losses"""
        consecutive_wins = []
        consecutive_losses = []
        current_streak = 0
        
        for t in trades:
            if t.get('pnl', 0) > 0:  # Winning trade
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
            else:  # Losing trade
                if current_streak < 0:
                    current_streak -= 1
                else:
                    if current_streak > 0:
                        consecutive_wins.append(current_streak)
                    current_streak = -1
                    
        # Add the final streak
        if current_streak > 0:
            consecutive_wins.append(current_streak)
        elif current_streak < 0:
            consecutive_losses.append(abs(current_streak))
            
        max_consecutive_wins = max(consecutive_wins) if consecutive_wins else 0
        max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0
        
        return {
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }
    
    @staticmethod
    def _analyze_exit_reasons(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze trade exit reasons"""
        exit_reasons = {}
        
        for t in trades:
            reason = t.get('exit_reason', 'unknown')
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
            
            exit_reasons[reason]['count'] += 1
            if t.get('pnl', 0) > 0:
                exit_reasons[reason]['wins'] += 1
            else:
                exit_reasons[reason]['losses'] += 1
            exit_reasons[reason]['pnl'] += t.get('pnl', 0)
        
        # Calculate win rate and average pnl for each exit reason
        for reason in exit_reasons:
            if exit_reasons[reason]['count'] > 0:
                exit_reasons[reason]['win_rate'] = (exit_reasons[reason]['wins'] / exit_reasons[reason]['count']) * 100
                exit_reasons[reason]['avg_pnl'] = exit_reasons[reason]['pnl'] / exit_reasons[reason]['count']
                
        return exit_reasons
