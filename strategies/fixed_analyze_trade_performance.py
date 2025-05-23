def analyze_trade_performance(self, entry_price, exit_price, side, trade_duration, trade_reason=""):
    """
    Analyze completed trade performance for strategy improvement.
    
    Parameters:
    -----------
    entry_price : float
        Entry price of the trade
    exit_price : float
        Exit price of the trade
    side : str
        'BUY' or 'SELL' trade direction
    trade_duration : float
        Duration of the trade in seconds/minutes/candles (based on implementation)
    trade_reason : str
        Reason for the trade exit
        
    Returns:
    --------
    dict
        Trade analysis metrics
    """
    try:
        # Calculate basic trade metrics
        if side == 'BUY':
            profit_pct = (exit_price - entry_price) / entry_price * 100
            profitable = exit_price > entry_price
        else:  # SELL (short)
            profit_pct = (entry_price - exit_price) / entry_price * 100
            profitable = exit_price < entry_price
            
        # Calculate reward-to-risk (assuming 2% risk)
        risk_amount = entry_price * (self.params.get('stop_loss_percentage', 0.5) / 100)
        if risk_amount > 0:
            if side == 'BUY':
                reward_to_risk = abs(exit_price - entry_price) / risk_amount
            else:
                reward_to_risk = abs(entry_price - exit_price) / risk_amount
        else:
            reward_to_risk = 0
            
        # Calculate trade return metrics
        if trade_duration > 0:
            # Simple ROI per time unit
            roi_per_minute = profit_pct / (trade_duration / 60) if trade_duration >= 60 else profit_pct
        else:
            roi_per_minute = 0
            
        # Create trade summary
        trade_summary = {
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_pct': profit_pct,
            'duration_minutes': trade_duration / 60 if trade_duration >= 60 else trade_duration,
            'profitable': profitable,
            'reward_to_risk': reward_to_risk,
            'roi_per_minute': roi_per_minute,
            'exit_reason': trade_reason
        }
        
        # Log the trade with appropriate level based on profitability
        if profitable:
            self.logger.info(f"Profitable {side} trade: {profit_pct:.2f}%, duration: {trade_summary['duration_minutes']:.1f} minutes")
        else:
            self.logger.info(f"Unprofitable {side} trade: {profit_pct:.2f}%, duration: {trade_summary['duration_minutes']:.1f} minutes")
        
        return trade_summary
        
    except Exception as e:
        self.logger.error(f"Error analyzing trade performance: {str(e)}")
        self.logger.debug(traceback.format_exc())
        return {'error': str(e)}
