#!/usr/bin/env python3
"""
Test script to verify that the trading bot can be initialized without real API access.
"""

import os
import sys
import logging
from datetime import datetime

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot_init_tester")

def test_bot_init():
    """Test if the trading bot can be initialized."""
    try:
        # Add the project directory to the path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import the TradingBot class
        from bot import TradingBot
        
        logger.info("Successfully imported TradingBot class")
        
        # Create a config for testing that doesn't require API access
        test_config = {
            'exchange': {
                'name': 'binance',
                'testnet': True
            },
            'general': {
                'telegram_notifications': False,
                'log_level': 'INFO'
            },
            'trading_pairs': [
                {
                    'symbol': 'BTCUSDT',
                    'quote_asset': 'USDT',
                    'base_asset': 'BTC',
                    'allocation': 0.3,
                    'min_quantity': 0.0001,
                    'price_precision': 2,
                    'quantity_precision': 5
                }
            ],
            'risk_management': {
                'max_open_trades_per_pair': 1,
                'max_daily_trades': 10,
                'max_capital_allocation': 0.5,
                'stop_loss_percentage': 1.0,
                'take_profit_percentage': 2.0
            },
            'strategy': {
                'timeframe': '1m',
                'ema_fast': 8,
                'ema_slow': 21,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
        }
        
        # Create a temporary config file
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w+', delete=False) as temp:
            yaml.dump(test_config, temp)
            temp_config_path = temp.name
            
        logger.info(f"Created temporary config file at {temp_config_path}")
        
        # Try to initialize the bot with mock functionality
        try:
            # Patch the initialize_client method to avoid API calls
            original_init_client = TradingBot.initialize_client
            
            def mock_init_client(self):
                self.logger.info("Mock client initialized")
                self.client = type('obj', (object,), {
                    'get_server_time': lambda: {'serverTime': int(datetime.now().timestamp() * 1000)},
                    'get_account': lambda: {'balances': [{'asset': 'USDT', 'free': '1000.0'}]}
                })
                
            TradingBot.initialize_client = mock_init_client
            
            # Initialize the bot
            bot = TradingBot(config_path=temp_config_path)
            logger.info("Successfully initialized TradingBot instance")
            
            # Restore original method
            TradingBot.initialize_client = original_init_client
            
            # Clean up
            os.unlink(temp_config_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            # Clean up
            os.unlink(temp_config_path)
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bot_init()
    if success:
        print("\n✅ Bot initialization test passed!")
    else:
        print("\n❌ Bot initialization test failed!")
    sys.exit(0 if success else 1)
