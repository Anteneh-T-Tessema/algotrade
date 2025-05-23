"""
This file contains the fixed version of the backtest_performance method for ScalpingStrategy
that properly integrates the BacktestEnhancer for performance metrics calculation.
"""

def backtest_performance(self, historical_data, market_data=None):
    """
    Run a comprehensive backtest of the strategy on historical data and return detailed performance metrics.
    
    Parameters:
    -----------
    historical_data : pandas.DataFrame
        Historical OHLCV data for backtesting
    market_data : dict, optional
        Dictionary of market indices/indicators DataFrames for correlation analysis
        
    Returns:
    --------
    dict
        Performance metrics including:
        - total_trades: Number of executed trades
        - win_rate: Percentage of profitable trades
        - profit_factor: Gross profit / gross loss
        - avg_profit: Average profit per winning trade
        - avg_loss: Average loss per losing trade
        - max_drawdown: Maximum drawdown percentage
        - sharpe_ratio: Risk-adjusted return metric
        - sortino_ratio: Downside risk-adjusted return metric
        - trade_durations: Average, min and max trade durations
        - monthly_returns: Performance broken down by month
        - win_streak: Longest winning streak
        - loss_streak: Longest losing streak
        - market_condition_performance: Performance breakdown by market condition
        - exit_reason_analysis: Analysis of trade exits by reason
    """
    try:
        self.logger.info("Starting comprehensive strategy backtest")
        
        # Ensure we have required data
        if historical_data is None or len(historical_data) < 50:
            self.logger.error("Insufficient historical data for backtesting")
            return {'error': 'Insufficient data'}
            
        # Initialize tracking variables
        trades = []
        position = None
        balance = 10000  # Starting with $10,000
        initial_balance = balance
        equity_curve = []
        equity_curve_dates = []
        daily_returns = {}  # Track daily returns
        monthly_returns = {}  # Track monthly returns
        volatility_trades = {}  # Track performance by volatility level
        correlation_trades = {}  # Track performance by market correlation
        
        # Win/loss streak tracking
        current_win_streak = 0
        current_loss_streak = 0
        win_streak = 0
        loss_streak = 0
        
        # Track maximum balance to calculate drawdown
        max_balance = balance
        max_drawdown = 0
        drawdown_duration = 0
        max_drawdown_duration = 0
        drawdown_start_balance = balance
        
        # Calculate indicators once for the entire dataset
        df = self.calculate_indicators(historical_data.copy())
        
        # Process each candle
        for i in range(30, len(df)):  # Skip first 30 candles to ensure indicators are calculated
            # Get current candle slice
            candle_data = df.iloc[:i+1]
            current_candle = candle_data.iloc[-1]
            current_price = current_candle['close']
            current_time = df.index[i] if hasattr(df, 'index') else i
            
            # Apply adaptive parameters to current market conditions
            adjusted_params = self.adapt_parameters_to_volatility(candle_data)
            current_volatility = getattr(self, 'current_volatility', {}).get('level', 'normal')
            
            # If market data provided, analyze broader market correlation
            market_bias = 'neutral'
            if market_data is not None:
                # Get subset of market data up to current point
                current_market_data = {}
                for symbol, symbol_data in market_data.items():
                    if symbol_data is not None and len(symbol_data) > i:
                        current_market_data[symbol] = symbol_data.iloc[:i+1]
                
                if current_market_data:
                    correlation_analysis = self.analyze_market_correlation(candle_data, current_market_data)
                    market_bias = correlation_analysis['recommendation']
            
            # Track equity after each candle
            equity_curve.append(balance)
            if hasattr(current_time, 'date'):
                equity_curve_dates.append(current_time)
            else:
                equity_curve_dates.append(None)
            
            # Track daily returns
            trade_date = current_time.date() if hasattr(current_time, 'date') else None
            if trade_date is not None:
                # Initialize daily return tracking if it's a new day
                if trade_date not in daily_returns:
                    daily_returns[trade_date] = {'start_balance': balance, 'end_balance': balance}
                else:
                    # Update end balance for this day
                    daily_returns[trade_date]['end_balance'] = balance
                
                # Track monthly returns
                month_key = f"{trade_date.year}-{trade_date.month:02d}"
                if month_key not in monthly_returns:
                    monthly_returns[month_key] = {'start_balance': balance, 'end_balance': balance, 'trades': 0, 'profitable_trades': 0}
                else:
                    monthly_returns[month_key]['end_balance'] = balance
            
            # Update drawdown calculation
            if balance > max_balance:
                max_balance = balance
                drawdown_duration = 0  # Reset duration since we hit a new high
                drawdown_start_balance = balance
            else:
                current_drawdown = (max_balance - balance) / max_balance * 100 if max_balance > 0 else 0
                max_drawdown = max(max_drawdown, current_drawdown)
                
                # Track drawdown duration
                if current_drawdown > 0:
                    drawdown_duration += 1
                    max_drawdown_duration = max(max_drawdown_duration, drawdown_duration)
            
            # If in position, check for exit
            if position is not None:
                # Calculate unrealized P&L
                if position['side'] == 'BUY':
                    unrealized_pnl = (current_price - position['entry_price']) * position['size']
                else:  # SELL (short)
                    unrealized_pnl = (position['entry_price'] - current_price) * position['size']
                    
                # Update position's maximum price for trailing stop
                if position['side'] == 'BUY':
                    position['max_price'] = max(position['max_price'], current_price)
                else:  # SELL (short)
                    position['max_price'] = min(position['max_price'], current_price)
                    
                # Calculate trailing stop with adjusted parameters
                atr = current_candle['atr'] if 'atr' in current_candle and not pd.isna(current_candle['atr']) else None
                trailing_stop = self.calculate_trailing_stop(
                    current_price, 
                    position['entry_price'], 
                    position['max_price'], 
                    position['side'], 
                    atr
                )
                
                # Check for trailing stop hit
                exit_signal = False
                exit_reason = ""
                
                if trailing_stop is not None:
                    if (position['side'] == 'BUY' and current_price < trailing_stop) or \
                       (position['side'] == 'SELL' and current_price > trailing_stop):
                        exit_signal = True
                        exit_reason = "trailing_stop"
                
                # Also check for counter-trend signal exit with market correlation bias
                signal = self.generate_signal(candle_data, {'market_bias': market_bias})
                trend_consistency = self.calculate_trend_consistency(candle_data)
                
                if (position['side'] == 'BUY' and signal == 'SELL' and trend_consistency < 0) or \
                   (position['side'] == 'SELL' and signal == 'BUY' and trend_consistency > 0):
                    exit_signal = True
                    exit_reason = "counter_trend"
                    
                # Take profit target with dynamic adjustment based on volatility
                take_profit_pct = adjusted_params.get('take_profit_percentage', 1.0) / 100
                if position['side'] == 'BUY':
                    take_profit = position['entry_price'] * (1 + take_profit_pct)
                    if current_price >= take_profit:
                        exit_signal = True
                        exit_reason = "take_profit"
                else:  # SELL
                    take_profit = position['entry_price'] * (1 - take_profit_pct)
                    if current_price <= take_profit:
                        exit_signal = True
                        exit_reason = "take_profit"
                
                # Check for time-based exit (after holding for a specific period)
                max_hold_period = 20  # Maximum candles to hold a position
                if i - position['entry_index'] >= max_hold_period:
                    exit_signal = True
                    exit_reason = "time_exit"
                        
                # Exit position if signal triggered
                if exit_signal:
                    # Calculate trade P&L
                    if position['side'] == 'BUY':
                        trade_pnl = (current_price - position['entry_price']) * position['size']
                    else:  # SELL (short)
                        trade_pnl = (position['entry_price'] - current_price) * position['size']
                        
                    # Update balance
                    balance += trade_pnl
                    
                    # Record trade details
                    trade_duration = i - position['entry_index']
                    
                    trade = {
                        'entry_time': position['entry_time'],
                        'exit_time': current_time,
                        'side': position['side'],
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'size': position['size'],
                        'pnl': trade_pnl,
                        'pnl_percentage': (trade_pnl / (position['entry_price'] * position['size'])) * 100,
                        'duration': trade_duration,
                        'exit_reason': exit_reason,
                        'market_volatility': position['market_volatility'],
                        'market_bias': position['market_bias'],
                        'risk_pct': position['risk_pct']
                    }
                    
                    trades.append(trade)
                    
                    # Update streak tracking
                    is_win = trade_pnl > 0
                    
                    if is_win:
                        current_win_streak += 1
                        current_loss_streak = 0
                        win_streak = max(win_streak, current_win_streak)
                    else:
                        current_loss_streak += 1
                        current_win_streak = 0
                        loss_streak = max(loss_streak, current_loss_streak)
                    
                    # Update monthly trade statistics if available
                    if trade_date is not None:
                        month_key = f"{trade_date.year}-{trade_date.month:02d}"
                        if month_key in monthly_returns:
                            monthly_returns[month_key]['trades'] += 1
                            if is_win:
                                monthly_returns[month_key]['profitable_trades'] += 1
                    
                    # Track trades by market condition
                    # By volatility
                    vol = position['market_volatility']
                    if vol not in volatility_trades:
                        volatility_trades[vol] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
                    volatility_trades[vol]['count'] += 1
                    if is_win:
                        volatility_trades[vol]['wins'] += 1
                    else:
                        volatility_trades[vol]['losses'] += 1
                    volatility_trades[vol]['pnl'] += trade_pnl
                    
                    # By correlation/market bias
                    bias = position['market_bias']
                    if bias not in correlation_trades:
                        correlation_trades[bias] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
                    correlation_trades[bias]['count'] += 1
                    if is_win:
                        correlation_trades[bias]['wins'] += 1
                    else:
                        correlation_trades[bias]['losses'] += 1
                    correlation_trades[bias]['pnl'] += trade_pnl
                    
                    position = None
                    
            # If not in position, check for entry signal
            else:
                signal = self.generate_signal(candle_data, {'market_bias': market_bias})
                
                if signal in ['BUY', 'SELL']:
                    # Calculate position size with adaptive parameters
                    # Adjust risk based on market volatility and correlation
                    base_risk = 0.02  # 2% base risk per trade
                    
                    # Adjust risk based on volatility
                    volatility_level = current_volatility
                    volatility_risk_factor = {
                        'very_low': 1.5,  # More aggressive in low volatility
                        'low': 1.2,
                        'normal': 1.0,
                        'high': 0.8,
                        'extreme': 0.6   # More conservative in high volatility
                    }.get(volatility_level, 1.0)
                    
                    # Adjust risk based on market correlation
                    correlation_risk_factor = 1.0
                    if (signal == 'BUY' and market_bias in ['bias_long', 'favor_long']):
                        correlation_risk_factor = 1.2  # More aggressive when aligned with market
                    elif (signal == 'SELL' and market_bias in ['bias_short', 'favor_short']):
                        correlation_risk_factor = 1.2  # More aggressive when aligned with market
                    elif (signal == 'BUY' and market_bias in ['bias_short', 'favor_short']):
                        correlation_risk_factor = 0.8  # More conservative when against market
                    elif (signal == 'SELL' and market_bias in ['bias_long', 'favor_long']):
                        correlation_risk_factor = 0.8  # More conservative when against market
                    
                    # Calculate final risk percentage
                    risk_pct = base_risk * volatility_risk_factor * correlation_risk_factor
                    risk_pct = min(0.04, max(0.01, risk_pct))  # Limit between 1% and 4%
                    
                    risk_amount = balance * risk_pct
                    atr = current_candle['atr'] if 'atr' in current_candle and not pd.isna(current_candle['atr']) else None
                    
                    # Get stop loss for position sizing
                    stop_loss, _ = self.calculate_exit_points(current_price, signal, atr)
                    
                    if stop_loss is not None:
                        risk_per_unit = abs(current_price - stop_loss)
                        size = risk_amount / risk_per_unit if risk_per_unit > 0 else balance * 0.01 / current_price
                    else:
                        # Default 1% position size if can't calculate risk
                        size = balance * 0.01 / current_price
                        
                    # Limit to max 10% of balance
                    size = min(size, balance * 0.1 / current_price)
                    
                    # Create new position
                    position = {
                        'side': signal,
                        'entry_price': current_price,
                        'size': size,
                        'entry_index': i,
                        'entry_time': current_time,
                        'max_price': current_price,  # For tracking trailing stop
                        'market_volatility': volatility_level,
                        'market_bias': market_bias,
                        'risk_pct': risk_pct * 100  # Store as percentage
                    }
        
        # Close any remaining open position at the end
        if position is not None:
            last_price = df.iloc[-1]['close']
            
            # Calculate trade P&L
            if position['side'] == 'BUY':
                trade_pnl = (last_price - position['entry_price']) * position['size']
            else:  # SELL (short)
                trade_pnl = (position['entry_price'] - last_price) * position['size']
                
            # Update balance
            balance += trade_pnl
            
            # Record trade
            trade_duration = len(df) - 1 - position['entry_index']
            
            trade = {
                'entry_time': position['entry_time'],
                'exit_time': df.index[-1] if hasattr(df, 'index') else len(df) - 1,
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': last_price,
                'size': position['size'],
                'pnl': trade_pnl,
                'pnl_percentage': (trade_pnl / (position['entry_price'] * position['size'])) * 100,
                'duration': trade_duration,
                'exit_reason': 'end_of_data',
                'market_volatility': position['market_volatility'],
                'market_bias': position['market_bias'],
                'risk_pct': position['risk_pct']
            }
            
            trades.append(trade)
        
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
        
        # Log comprehensive results summary
        self.logger.info(f"Backtest completed with {total_trades} trades over {len(daily_returns) if daily_returns else 'N/A'} days")
        self.logger.info(f"Win rate: {win_rate:.2f}%, Profit factor: {profit_factor:.2f}, Expectancy: {expectancy:.2f}%")
        self.logger.info(f"Net profit: ${net_profit:.2f} ({results['net_profit_percent']:.2f}%)")
        self.logger.info(f"Max drawdown: {max_drawdown:.2f}%, Max drawdown duration: {max_drawdown_duration} candles")
        self.logger.info(f"Sharpe ratio: {sharpe_ratio:.2f}, Sortino ratio: {sortino_ratio:.2f}")
        self.logger.info(f"Win/Loss streak: {max_consecutive_wins}/{max_consecutive_losses}")
        
        # Log monthly performance summary
        if monthly_performance:
            self.logger.info("Monthly performance summary:")
            for month, perf in sorted(monthly_performance.items()):
                self.logger.info(f"  {month}: {perf['return_pct']:.2f}% (Trades: {perf['trades']}, Win rate: {perf['win_rate']:.1f}%)")
        
        # Log exit reason analysis
        self.logger.info("Exit reason analysis:")
        for reason, stats in exit_reasons.items():
            self.logger.info(f"  {reason}: {stats['count']} trades, Win rate: {stats['win_rate']:.1f}%, Avg P/L: ${stats['avg_pnl']:.2f}")
        
        # Log volatility analysis
        self.logger.info("Performance by volatility level:")
        for vol, stats in results['volatility_analysis'].items():
            self.logger.info(f"  {vol}: {stats['count']} trades, Win rate: {stats['win_rate']:.1f}%, Avg P/L: ${stats['avg_pnl']:.2f}")
        
        return results
        
    except Exception as e:
        self.logger.error(f"Error in backtest: {str(e)}")
        self.logger.debug(traceback.format_exc())
        return {'error': str(e)}
