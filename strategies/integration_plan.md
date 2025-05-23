# Integration Plan: BacktestEnhancer for ScalpingStrategy

## Overview
This document outlines the steps to properly integrate the BacktestEnhancer with the ScalpingStrategy's backtest_performance method to leverage enhanced backtesting capabilities.

## Current Status
- The BacktestEnhancer class is already imported in scalping_strategy.py
- The backtest_performance method is manually calculating metrics instead of leveraging the BacktestEnhancer

## Required Changes

### 1. Replace manual metric calculation with BacktestEnhancer

Find this code section in backtest_performance method (after collecting trades):
```python
# Calculate performance metrics
if len(trades) == 0:
    self.logger.warning("No trades executed in backtest")
    return {'error': 'No trades executed'}

# Basic metrics
total_trades = len(trades)
winning_trades = [t for t in trades if t['pnl'] > 0]
losing_trades = [t for t in trades if t['pnl'] <= 0]

# ... many more calculations ...
```

Replace with:
```python
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
```

### 2. Remove the results dictionary creation

Find this code section:
```python
# Prepare comprehensive result dictionary
results = {
    # Basic trade metrics
    'total_trades': total_trades,
    'win_rate': win_rate,
    # ... many more metrics ...
}
```

This section should be removed since BacktestEnhancer already returns the complete results dictionary.

### 3. Update Volatility Analysis Logging

Update the volatility analysis logging section:

From:
```python
# Log volatility analysis
self.logger.info("Performance by volatility level:")
for vol, stats in volatility_trades.items():
    self.logger.info(f"  {vol}: {stats['count']} trades, Win rate: {stats['win_rate']:.1f}%, Avg P/L: ${stats['avg_pnl']:.2f}")
```

To:
```python
# Log volatility analysis
self.logger.info("Performance by volatility level:")
for vol, stats in results['volatility_analysis'].items():
    self.logger.info(f"  {vol}: {stats['count']} trades, Win rate: {stats['win_rate']:.1f}%, Avg P/L: ${stats['avg_pnl']:.2f}")
```

## Benefits of Using BacktestEnhancer
1. More comprehensive performance metrics
2. Better code organization and separation of concerns
3. Consistent metrics calculation across different strategies
4. Enhanced risk metrics (Sharpe ratio, Sortino ratio)
5. In-depth analysis by market conditions (volatility, correlation)

## Testing After Integration
After implementing these changes, test the ScalpingStrategy with a sample backtest to verify:
1. All metrics are correctly calculated
2. No errors occur during the backtesting process
3. The output format is consistent with other strategies
