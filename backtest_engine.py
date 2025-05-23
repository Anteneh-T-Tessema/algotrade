#!/usr/bin/env python3
"""
Advanced Backtesting Engine

This module provides a more sophisticated backtesting engine with:
- Virtual position tracking
- P&L calculation and drawdown monitoring
- Comprehensive metrics and statistics
- Equity curve generation and visualization
- Walk-forward analysis capabilities
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Any, Optional
import json

from strategies.base_strategy import Strategy, Position, PositionSide
from utils.history_loader import HistoryLoader


class BacktestEngine:
    """
    Advanced backtesting engine for trading strategies
    """
    
    def __init__(self, strategy: Strategy, initial_capital: float = 10000.0, logger=None):
        """
        Initialize the backtesting engine
        
        Parameters:
        -----------
        strategy : Strategy
            Trading strategy to test
        initial_capital : float
            Initial capital for backtesting
        logger : logging.Logger, optional
            Logger instance
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.logger = logger or logging.getLogger(__name__)
        
        # Performance tracking
        self.positions = []
        self.current_position = None
        self.equity_curve = [initial_capital]
        self.equity_timestamps = []
        self.trades_history = []
        
        # Drawdown tracking
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.peak_capital = initial_capital
        
    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run a backtest on historical data
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Historical price data with required indicators
            
        Returns:
        --------
        dict
            Backtest results
        """
        self.logger.info(f"Running backtest for {self.strategy.name} strategy")
        self.logger.info(f"Initial capital: ${self.initial_capital}")
        
        # Reset state before running
        self._reset()
        
        # Add initial equity point
        if len(data) > 0:
            self.equity_timestamps.append(data.index[0])
        
        # Main backtest loop
        for i in range(1, len(data)):
            current_time = data.index[i]
            previous_candle = data.iloc[i-1]
            current_candle = data.iloc[i]
            
            # Update current position if exists
            if self.current_position:
                # Check for stop-loss and take-profit
                position_closed = self.current_position.update(current_candle['open'], current_time)
                
                if position_closed:
                    # Position was closed by stop-loss or take-profit
                    self._close_position(self.current_position.exit_price, current_time)
            
            # Check for strategy signals
            action = self.strategy.on_candle(current_candle, self.current_capital)
            
            if action:
                if action['action'] == 'BUY' and self.current_position is None:
                    self._open_position(current_time, action['price'], action['size'], 
                                       PositionSide.LONG, action.get('stop_loss'), action.get('take_profit'))
                    
                elif action['action'] == 'SELL' and self.current_position is not None:
                    self._close_position(action['price'], current_time)
            
            # Update equity curve at each step
            self._update_equity(current_time, current_candle['close'])
        
        # Close any remaining positions at the end of the backtest
        if self.current_position:
            last_price = data.iloc[-1]['close']
            last_time = data.index[-1]
            self._close_position(last_price, last_time)
        
        # Calculate and return metrics
        return self._calculate_metrics(data)
    
    def _open_position(self, timestamp, price, size, side, stop_loss=None, take_profit=None):
        """Open a new position"""
        if self.current_position:
            self.logger.warning(f"Attempting to open position while another is still active")
            return
            
        self.current_position = Position(self.strategy.name, price, size, side)
        self.current_position.entry_time = timestamp
        self.current_position.stop_loss = stop_loss
        self.current_position.take_profit = take_profit
        
        self.current_capital = self.current_capital - (price * size)  # Reduce capital by position cost
        
        self.logger.info(f"Opened {side.value} position: {size:.6f} @ ${price:.2f}")
        if stop_loss:
            self.logger.info(f"Stop Loss: ${stop_loss:.2f}")
        if take_profit:
            self.logger.info(f"Take Profit: ${take_profit:.2f}")
    
    def _close_position(self, price, timestamp):
        """Close the current position"""
        if not self.current_position:
            self.logger.warning(f"Attempting to close position but no position is open")
            return
            
        # Calculate P&L
        profit_loss = self.current_position.close(price, timestamp)
        
        # Update capital
        self.current_capital += (price * self.current_position.size)
        
        # Log results
        pnl_percent = self.current_position.profit_loss_pct
        self.logger.info(f"Closed {self.current_position.side.value} position: {self.current_position.size:.6f} @ ${price:.2f}")
        self.logger.info(f"P&L: ${profit_loss:.2f} ({pnl_percent:.2f}%)")
        self.logger.info(f"Capital: ${self.current_capital:.2f}")
        
        # Add to trade history
        self.trades_history.append(self.current_position)
        self.positions.append(self.current_position)
        self.current_position = None
    
    def _update_equity(self, timestamp, current_price):
        """Update the equity curve and track drawdown"""
        current_equity = self.current_capital
        
        # Add unrealized P&L if we have an open position
        if self.current_position:
            if self.current_position.side == PositionSide.LONG:
                unrealized_pnl = (current_price - self.current_position.entry_price) * self.current_position.size
            else:
                unrealized_pnl = (self.current_position.entry_price - current_price) * self.current_position.size
                
            current_equity += unrealized_pnl + (self.current_position.size * self.current_position.entry_price)
        
        # Update equity curve
        self.equity_curve.append(current_equity)
        self.equity_timestamps.append(timestamp)
        
        # Track drawdown
        if current_equity > self.peak_capital:
            self.peak_capital = current_equity
        else:
            drawdown = self.peak_capital - current_equity
            drawdown_pct = (drawdown / self.peak_capital) * 100
            
            if drawdown_pct > self.max_drawdown_pct:
                self.max_drawdown = drawdown
                self.max_drawdown_pct = drawdown_pct
    
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not self.trades_history:
            self.logger.warning("No trades executed during backtest")
            return {
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'total_return': 0,
                'total_trades': 0,
                'win_rate': 0,
                'equity_curve': self.equity_curve,
                'equity_timestamps': self.equity_timestamps,
                'max_drawdown_pct': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'avg_profit': 0, 
                'avg_loss': 0,
            }
        
        # Basic metrics
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        total_trades = len(self.trades_history)
        
        # Win/loss metrics
        winning_trades = [t for t in self.trades_history if t.profit_loss > 0]
        losing_trades = [t for t in self.trades_history if t.profit_loss <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit/loss metrics
        gross_profits = sum(t.profit_loss for t in winning_trades)
        gross_losses = abs(sum(t.profit_loss for t in losing_trades)) if losing_trades else 1e-10
        
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
        
        avg_profit = gross_profits / len(winning_trades) if winning_trades else 0
        avg_loss = gross_losses / len(losing_trades) if losing_trades else 0
        
        # Calculate returns based on equity curve
        if len(self.equity_curve) > 1:
            returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
            annual_factor = 252  # Trading days in a year
            
            # Risk-adjusted ratios
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
            sharpe_ratio = mean_return / std_return * np.sqrt(annual_factor) if std_return > 0 else 0
            
            # Sortino Ratio (only downside deviation)
            negative_returns = returns[returns < 0]
            downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 1e-10
            sortino_ratio = mean_return / downside_deviation * np.sqrt(annual_factor) if downside_deviation > 0 else 0
            
            # Calmar Ratio (return / max drawdown)
            calmar_ratio = (total_return / 100) / (self.max_drawdown_pct / 100) * annual_factor if self.max_drawdown_pct > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
            calmar_ratio = 0
            
        # Package metrics
        metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'total_return': total_return,
            'total_return_pct': total_return,  # For backward compatibility
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'equity_curve': self.equity_curve,
            'equity_timestamps': self.equity_timestamps,
        }
        
        return metrics
    
    def plot_results(self, save_path=None, show_plot=True):
        """
        Plot backtest results with equity curve and drawdown
        
        Parameters:
        -----------
        save_path : str, optional
            Path to save the plot
        show_plot : bool
            Whether to display the plot
        """
        if not self.equity_curve or len(self.equity_curve) < 2:
            self.logger.warning("Not enough data to generate plots")
            return
            
        # Create figure with subplots for equity curve and drawdown
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # Plot equity curve
        timestamps = [pd.to_datetime(ts) for ts in self.equity_timestamps]
        axes[0].plot(timestamps, self.equity_curve)
        axes[0].set_title(f"{self.strategy.name} - Equity Curve")
        axes[0].set_ylabel("Equity ($)")
        axes[0].grid(True)
        
        # Add annotations for trades if not too many
        if len(self.trades_history) > 0 and len(self.trades_history) < 50:
            for trade in self.trades_history:
                if trade.profit_loss > 0:
                    color = 'green'
                    marker = '^' if trade.side == PositionSide.LONG else 'v'
                else:
                    color = 'red'
                    marker = 'v' if trade.side == PositionSide.LONG else '^'
                    
                # Find the equity at trade exit
                idx = self.equity_timestamps.index(trade.exit_time)
                equity = self.equity_curve[idx]
                
                axes[0].scatter(pd.to_datetime(trade.exit_time), equity, color=color, marker=marker, s=50, zorder=5)
        
        # Calculate and plot drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (running_max - equity_array) / running_max * 100
        
        axes[1].fill_between(timestamps, 0, drawdown, color='red', alpha=0.3)
        axes[1].set_title("Drawdown (%)")
        axes[1].set_ylabel("Drawdown %")
        axes[1].set_ylim(bottom=0, top=max(drawdown) * 1.1)
        axes[1].grid(True)
        
        # Format x-axis
        for ax in axes:
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Save plot if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Plot saved to: {save_path}")
            
        # Show plot if requested
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def generate_report(self, output_file=None):
        """
        Generate a detailed text report of backtest results
        
        Parameters:
        -----------
        output_file : str, optional
            Path to save the report
        """
        # Calculate metrics if not already done
        metrics = self._calculate_metrics(None)
        
        # Format the report
        report = []
        report.append("=" * 80)
        report.append(f"BACKTEST RESULTS - {self.strategy.name}")
        report.append("=" * 80)
        report.append(f"Period: {self.equity_timestamps[0]} to {self.equity_timestamps[-1]}")
        report.append(f"Initial Capital: ${self.initial_capital:.2f}")
        report.append(f"Final Capital: ${self.current_capital:.2f}")
        report.append(f"Total Return: {metrics['total_return']:.2f}%")
        report.append("-" * 80)
        report.append("TRADE STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Trades: {metrics['total_trades']}")
        report.append(f"Win Rate: {metrics['win_rate'] * 100:.2f}%")
        report.append(f"Profit Factor: {metrics['profit_factor']:.2f}")
        report.append(f"Average Profit: ${metrics['avg_profit']:.2f}")
        report.append(f"Average Loss: ${metrics['avg_loss']:.2f}")
        report.append("-" * 80)
        report.append("RISK METRICS")
        report.append("-" * 80)
        report.append(f"Maximum Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        report.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        report.append(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        report.append(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
        
        # Add trade list
        if self.trades_history:
            report.append("-" * 80)
            report.append("TRADE LIST")
            report.append("-" * 80)
            report.append("{:<25} {:<7} {:<10} {:<10} {:<10} {:<10}".format(
                "Date", "Side", "Entry", "Exit", "P&L", "P&L%"
            ))
            report.append("-" * 80)
            
            for trade in self.trades_history:
                report.append("{:<25} {:<7} {:<10.2f} {:<10.2f} {:<10.2f} {:<10.2f}%".format(
                    str(trade.entry_time),
                    trade.side.value,
                    trade.entry_price,
                    trade.exit_price,
                    trade.profit_loss,
                    trade.profit_loss_pct
                ))
        
        report_str = "\n".join(report)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_str)
            self.logger.info(f"Report saved to: {output_file}")
        
        return report_str
    
    def save_results(self, filepath):
        """
        Save backtest results to JSON file
        
        Parameters:
        -----------
        filepath : str
            Path to save the results
        """
        metrics = self._calculate_metrics(None)
        
        # Convert timestamps and non-serializable types
        serializable_metrics = {}
        for key, value in metrics.items():
            if key == 'equity_timestamps':
                serializable_metrics[key] = [str(ts) for ts in value]
            elif isinstance(value, np.ndarray):
                serializable_metrics[key] = value.tolist()
            elif isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                serializable_metrics[key] = str(value)
            else:
                serializable_metrics[key] = value
        
        # Add strategy info
        serializable_metrics['strategy'] = self.strategy.name
        serializable_metrics['strategy_params'] = self.strategy.params
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(serializable_metrics, f, indent=4)
            
        self.logger.info(f"Results saved to: {filepath}")
    
    def _reset(self):
        """Reset the backtesting state"""
        self.current_capital = self.initial_capital
        self.positions = []
        self.current_position = None
        self.equity_curve = [self.initial_capital]
        self.equity_timestamps = []
        self.trades_history = []
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.peak_capital = self.initial_capital


def run_walk_forward(strategy_class, data, params_list, initial_capital=10000, window_size=100,
                   step_size=20, validation_size=30, logger=None):
    """
    Run a walk-forward optimization of a strategy
    
    Parameters:
    -----------
    strategy_class : type
        Strategy class to instantiate
    data : pandas.DataFrame
        Full historical dataset
    params_list : list
        List of parameter sets to test
    initial_capital : float
        Initial capital for backtesting
    window_size : int
        Size of each training window (in candles)
    step_size : int
        How many candles to move forward for each iteration
    validation_size : int
        Size of validation windows (in candles)
    logger : logging.Logger, optional
        Logger instance
    
    Returns:
    --------
    dict
        Walk-forward optimization results
    """
    logger = logger or logging.getLogger(__name__)
    logger.info("Starting walk-forward optimization")
    
    results = []
    windows = []
    best_params_over_time = []
    
    # Ensure we have enough data
    if len(data) < window_size + validation_size:
        logger.error(f"Not enough data for walk-forward optimization. "
                    f"Need at least {window_size + validation_size} candles, but got {len(data)}")
        return None
    
    # Split data into training/validation windows
    for start_idx in range(0, len(data) - window_size - validation_size, step_size):
        train_end = start_idx + window_size
        valid_end = train_end + validation_size
        
        train_data = data.iloc[start_idx:train_end]
        validation_data = data.iloc[train_end:valid_end]
        
        windows.append({
            'train_start': data.index[start_idx],
            'train_end': data.index[train_end - 1],
            'valid_start': data.index[train_end],
            'valid_end': data.index[valid_end - 1] if valid_end <= len(data) else data.index[-1],
            'train_data': train_data,
            'validation_data': validation_data
        })
    
    # Run optimization for each window
    for i, window in enumerate(windows):
        logger.info(f"Window {i+1}/{len(windows)}: "
                   f"{window['train_start']} to {window['train_end']} (training), "
                   f"{window['valid_start']} to {window['valid_end']} (validation)")
        
        # Find best parameters on training data
        best_return = -float('inf')
        best_params = None
        
        for params in params_list:
            strategy = strategy_class(f"{strategy_class.__name__}", params)
            engine = BacktestEngine(strategy, initial_capital)
            
            # Run on training data
            train_results = engine.run(window['train_data'])
            
            if train_results['total_return'] > best_return:
                best_return = train_results['total_return']
                best_params = params
        
        # Run best parameters on validation data
        strategy = strategy_class(f"{strategy_class.__name__}", best_params)
        engine = BacktestEngine(strategy, initial_capital)
        valid_results = engine.run(window['validation_data'])
        
        # Store results
        results.append({
            'window': i + 1,
            'train_start': window['train_start'],
            'train_end': window['train_end'],
            'valid_start': window['valid_start'],
            'valid_end': window['valid_end'],
            'best_params': best_params,
            'train_return': best_return,
            'validation_return': valid_results['total_return']
        })
        
        best_params_over_time.append(best_params)
        
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Training return: {best_return:.2f}%")
        logger.info(f"Validation return: {valid_results['total_return']:.2f}%")
    
    # Calculate stability and performance metrics
    params_stability = analyze_parameter_stability(best_params_over_time)
    
    logger.info(f"Walk-forward optimization complete. {len(windows)} windows analyzed.")
    
    return {
        'windows': len(windows),
        'results': results,
        'params_stability': params_stability,
        'best_params_over_time': best_params_over_time
    }

def analyze_parameter_stability(params_list):
    """
    Analyze the stability of parameters across walk-forward windows
    
    Parameters:
    -----------
    params_list : list
        List of parameter dictionaries
    
    Returns:
    --------
    dict
        Parameter stability analysis
    """
    if not params_list:
        return {}
    
    # Extract all parameter names
    param_names = set()
    for params in params_list:
        param_names.update(params.keys())
    
    # Calculate statistics for each parameter
    stats = {}
    for param in param_names:
        values = [p.get(param) for p in params_list if param in p]
        if not values:
            continue
            
        # Only calculate statistics for numerical parameters
        if all(isinstance(v, (int, float)) for v in values):
            stats[param] = {
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values),
                'min': min(values),
                'max': max(values),
                'stability': 1 - (np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0
            }
    
    return stats
