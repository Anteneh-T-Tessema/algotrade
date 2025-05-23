from datetime import datetime, time

class RiskManager:
    """Risk management class to enforce trading limits and risk controls."""
    
    def __init__(self, config, logger):
        """Initialize the risk manager with configuration."""
        self.config = config
        self.logger = logger
        self.daily_trades = {}
        self.open_trades_count = {}
        
    def can_open_new_trade(self, symbol, active_trades):
        """Check if a new trade can be opened based on risk parameters."""
        current_date = datetime.now().date()
        
        # Reset daily counters if it's a new day
        if current_date not in self.daily_trades:
            self.daily_trades = {current_date: 0}
            
        # Update open trades counter
        self.open_trades_count = {}
        for trade_id, trade in active_trades.items():
            if trade['status'] == 'OPEN':
                if trade['symbol'] not in self.open_trades_count:
                    self.open_trades_count[trade['symbol']] = 0
                self.open_trades_count[trade['symbol']] += 1
        
        # Check max open trades per pair
        max_open_trades_per_pair = self.config.get('max_open_trades_per_pair', 1)
        if self.open_trades_count.get(symbol, 0) >= max_open_trades_per_pair:
            self.logger.info(f"Maximum open trades reached for {symbol}")
            return False
            
        # Check max daily trades
        max_daily_trades = self.config.get('max_daily_trades', 100)
        if self.daily_trades.get(current_date, 0) >= max_daily_trades:
            self.logger.info(f"Maximum daily trades reached ({max_daily_trades})")
            return False
            
        # Increment daily trades counter
        self.daily_trades[current_date] = self.daily_trades.get(current_date, 0) + 1
        
        return True
        
    def calculate_position_size(self, symbol, price, balance, trading_pairs_config):
        """Calculate appropriate position size based on risk parameters."""
        # Find the trading pair config
        pair_config = next((pair for pair in trading_pairs_config if pair['symbol'] == symbol), None)
        if not pair_config:
            self.logger.error(f"No configuration found for {symbol}")
            return 0
            
        quote_asset = pair_config['quote_asset']
        available_balance = balance.get(quote_asset, 0)
        
        # Apply allocation percentage from config
        allocation = available_balance * pair_config['allocation'] * self.config['max_capital_allocation']
        
        # Calculate quantity
        quantity = allocation / price
        
        # Ensure minimum quantity
        if quantity < pair_config['min_quantity']:
            self.logger.info(f"Calculated quantity below minimum for {symbol}")
            return 0
            
        # Round to precision
        quantity = round(quantity, pair_config['quantity_precision'])
        
        return quantity
        
    def calculate_stop_loss(self, entry_price, side='BUY'):
        """Calculate stop loss price based on risk parameters."""
        stop_loss_pct = self.config.get('stop_loss_percentage', 1.0) / 100
        
        if side == 'BUY':
            return entry_price * (1 - stop_loss_pct)
        else:
            return entry_price * (1 + stop_loss_pct)
            
    def calculate_take_profit(self, entry_price, side='BUY'):
        """Calculate take profit price based on risk parameters."""
        take_profit_pct = self.config.get('take_profit_percentage', 2.0) / 100
        
        if side == 'BUY':
            return entry_price * (1 + take_profit_pct)
        else:
            return entry_price * (1 - take_profit_pct)
            
    def is_trading_allowed(self):
        """Check if trading is allowed based on time restrictions."""
        # Get current time
        now = datetime.now().time()
        
        # Parse start and end times
        start_time_str = self.config.get('trade_start_time', "00:00:00")
        end_time_str = self.config.get('trade_end_time', "23:59:59")
        
        start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
        
        # Check if current time is within trading hours
        return start_time <= now <= end_time
