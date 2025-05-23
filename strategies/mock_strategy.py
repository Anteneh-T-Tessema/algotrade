import numpy as np

class MockTradingStrategy:
    """
    A simplified mock strategy for backtesting without relying on complex indicators.
    This strategy generates predictable signals based on price oscillations.
    """
    
    def __init__(self, logger):
        """Initialize the mock strategy."""
        self.logger = logger
        
    def generate_signal(self, df):
        """
        Generate trading signals based on simple price movement patterns.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Dataframe with market data
            
        Returns:
        --------
        str
            'BUY', 'SELL', or 'HOLD' signal
        """
        if df.empty or len(df) < 5:  # Need a few candles
            return 'HOLD'
            
        # Get the latest candles
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Calculate a simple moving average
        last_prices = df['close'].iloc[-5:].values
        sma = np.mean(last_prices)
        
        # Simple crossing strategy
        if prev['close'] < sma and latest['close'] > sma:
            self.logger.info(f"BUY signal: Price {latest['close']} crossed above SMA {sma}")
            return 'BUY'
        elif prev['close'] > sma and latest['close'] < sma:
            self.logger.info(f"SELL signal: Price {latest['close']} crossed below SMA {sma}")
            return 'SELL'
        
        # Oversold/overbought based on simple price oscillation
        price_change_pct = (latest['close'] / df['close'].iloc[-5]) - 1
        
        if price_change_pct < -0.03:  # Down more than 3% in last 5 candles
            self.logger.info(f"BUY signal: Price dropped {price_change_pct*100:.2f}% (oversold)")
            return 'BUY'
        elif price_change_pct > 0.03:  # Up more than 3% in last 5 candles
            self.logger.info(f"SELL signal: Price rose {price_change_pct*100:.2f}% (overbought)")
            return 'SELL'
        
        return 'HOLD'
        
    def calculate_exit_points(self, entry_price, side='BUY'):
        """
        Calculate exit points (stop loss and take profit) based on the entry price.
        
        Parameters:
        -----------
        entry_price : float
            The entry price of the trade
        side : str
            'BUY' or 'SELL' to indicate trade direction
            
        Returns:
        --------
        tuple
            (stop_loss_price, take_profit_price)
        """
        # For long positions
        if side == 'BUY':
            stop_loss = entry_price * 0.99  # 1% stop loss
            take_profit = entry_price * 1.02  # 2% take profit
        # For short positions
        else:
            stop_loss = entry_price * 1.01  # 1% stop loss
            take_profit = entry_price * 0.98  # 2% take profit
            
        return stop_loss, take_profit
