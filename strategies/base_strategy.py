#!/usr/bin/env python3
"""
Base Strategy Class

This module defines the base strategy interface that all trading strategies should implement.
It provides common functionality for strategy development and backesting.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from enum import Enum

class PositionSide(Enum):
    """Position side enum (long or short)"""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"

class Position:
    """
    Represents a trading position with entry price, size, and side
    """
    def __init__(self, symbol, entry_price, size, side=PositionSide.LONG):
        self.symbol = symbol
        self.entry_price = entry_price
        self.size = size
        self.side = side
        self.entry_time = pd.Timestamp.now()
        self.exit_price = None
        self.exit_time = None
        self.profit_loss = 0
        self.profit_loss_pct = 0
        self.stop_loss = None
        self.take_profit = None
        self.exit_reason = None
    
    def close(self, exit_price, exit_time, reason="STRATEGY_SIGNAL"):
        """Close the position with an exit price"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason
        
        # Calculate P&L
        if self.side == PositionSide.LONG:
            self.profit_loss = (exit_price - self.entry_price) * self.size
            self.profit_loss_pct = (exit_price / self.entry_price - 1) * 100
        else:
            self.profit_loss = (self.entry_price - exit_price) * self.size
            self.profit_loss_pct = (self.entry_price / exit_price - 1) * 100
            
        return self.profit_loss
    
    def update(self, current_price, current_time):
        """
        Update the position's unrealized P&L based on current price
        Returns True if stop loss or take profit was triggered
        """
        # Skip if position is already closed
        if self.exit_price is not None:
            return False
            
        # Check stop loss
        if self.stop_loss is not None:
            if (self.side == PositionSide.LONG and current_price <= self.stop_loss) or \
               (self.side == PositionSide.SHORT and current_price >= self.stop_loss):
                self.close(self.stop_loss, current_time, "STOP_LOSS")
                return True
                
        # Check take profit
        if self.take_profit is not None:
            if (self.side == PositionSide.LONG and current_price >= self.take_profit) or \
               (self.side == PositionSide.SHORT and current_price <= self.take_profit):
                self.close(self.take_profit, current_time, "TAKE_PROFIT")
                return True
                
        return False
    
    def __str__(self):
        status = "OPEN" if self.exit_price is None else "CLOSED"
        if status == "OPEN":
            return f"{status} {self.side.value} {self.symbol} position: {self.size} @ {self.entry_price}"
        else:
            return f"{status} {self.side.value} {self.symbol} position: {self.size} @ {self.entry_price} -> {self.exit_price}, P&L: {self.profit_loss_pct:.2f}%, Reason: {self.exit_reason}"
            

class Strategy(ABC):
    """
    Base class for all trading strategies
    """
    
    def __init__(self, name, params=None):
        """
        Initialize the strategy with a name and optional parameters
        
        Parameters:
        -----------
        name : str
            Strategy name
        params : dict, optional
            Strategy parameters
        """
        self.name = name
        self.params = params or {}
        self.positions = []
        self.current_position = None
        self.equity_curve = []
        self.trades_history = []
        self.initial_capital = 0
        self.current_capital = 0
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.peak_capital = 0
        
    @abstractmethod
    def generate_signal(self, df):
        """
        Generate a trading signal based on market data
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with market data and indicators
            
        Returns:
        --------
        str
            'BUY', 'SELL', or 'HOLD' signal
        """
        pass
        
    @abstractmethod
    def calculate_indicators(self, df):
        """
        Calculate technical indicators used by the strategy
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame with raw market data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with added indicators
        """
        pass
        
    def on_candle(self, candle, balance):
        """
        Process a new candle and determine if any action should be taken
        
        Parameters:
        -----------
        candle : pandas.Series
            A single candle with OHLCV data and indicators
        balance : float
            Current account balance
            
        Returns:
        --------
        dict or None
            Trade action to take, or None if no action
            Example: {'action': 'BUY', 'price': 100, 'size': 1}
        """
        # This default implementation relies on the generate_signal method
        # Subclasses can override this method for more complex behavior
        signal = self.generate_signal(pd.DataFrame([candle]).T)
        
        current_price = candle['close']
        
        if signal == 'BUY' and self.current_position is None:
            # Calculate position size (using 95% of balance by default)
            size = (balance * 0.95) / current_price
            
            stop_loss, take_profit = self.calculate_exit_points(current_price, 'BUY')
            
            return {
                'action': 'BUY',
                'price': current_price,
                'size': size,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
        elif signal == 'SELL' and self.current_position is not None:
            return {
                'action': 'SELL',
                'price': current_price,
                'size': self.current_position.size
            }
            
        return None
        
    def calculate_exit_points(self, entry_price, side='BUY'):
        """
        Calculate stop loss and take profit prices
        
        Parameters:
        -----------
        entry_price : float
            Entry price
        side : str
            'BUY' or 'SELL'
            
        Returns:
        --------
        tuple
            (stop_loss_price, take_profit_price)
        """
        # Default implementation - override in subclasses
        stop_loss_pct = self.params.get('stop_loss_percentage', 1.0) / 100
        take_profit_pct = self.params.get('take_profit_percentage', 2.0) / 100
        
        if side == 'BUY':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - take_profit_pct)
            
        return stop_loss, take_profit
    
    def calculate_metrics(self):
        """
        Calculate strategy performance metrics
        
        Returns:
        --------
        dict
            Dictionary of performance metrics
        """
        if not self.trades_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'average_profit': 0,
                'average_loss': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0,
                'equity_curve': []
            }
            
        # Calculate trade stats
        total_trades = len(self.trades_history)
        winning_trades = [t for t in self.trades_history if t.profit_loss > 0]
        losing_trades = [t for t in self.trades_history if t.profit_loss <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = abs(sum(t.profit_loss for t in losing_trades)) if losing_trades else 1e-10
        
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_profit = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_profit': avg_profit,
            'average_loss': avg_loss,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': self.equity_curve
        }
        
    def reset(self):
        """Reset the strategy state"""
        self.positions = []
        self.current_position = None
        self.equity_curve = []
        self.trades_history = []
        self.initial_capital = 0
        self.current_capital = 0
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.peak_capital = 0
