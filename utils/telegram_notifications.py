import os
import telegram_send

class TelegramNotifier:
    """Sends notifications to Telegram."""
    
    def __init__(self, logger):
        """Initialize the telegram notifier."""
        self.logger = logger
        self.enabled = self._is_configured()
        
    def _is_configured(self):
        """Check if Telegram is properly configured."""
        telegram_token = os.environ.get('TELEGRAM_TOKEN')
        telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not telegram_token or not telegram_chat_id:
            self.logger.warning("Telegram notifications not configured properly")
            return False
            
        return True
        
    def send_notification(self, message):
        """Send a notification message to Telegram."""
        if not self.enabled:
            return
            
        try:
            # Check if telegram_send is configured
            try:
                telegram_send.send(messages=[message])
            except telegram_send.ConfigError:
                # Try to configure telegram_send with environment variables
                telegram_token = os.environ.get('TELEGRAM_TOKEN')
                telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
                
                if telegram_token and telegram_chat_id:
                    # Create a temporary config file
                    import tempfile
                    import configparser
                    
                    config = configparser.ConfigParser()
                    config['telegram'] = {
                        'token': telegram_token,
                        'chat_id': telegram_chat_id
                    }
                    
                    with tempfile.NamedTemporaryFile(suffix='.conf', mode='w+', delete=False) as temp:
                        config.write(temp)
                        temp_name = temp.name
                    
                    # Use the temp config file
                    telegram_send.send(messages=[message], conf=temp_name)
                    
                    # Clean up
                    os.unlink(temp_name)
                else:
                    raise ValueError("Telegram credentials not fully configured")
                    
            self.logger.debug(f"Telegram notification sent: {message}")
        except telegram_send.ConfigError as e:
            self.logger.error(f"Telegram config error: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Telegram value error: {str(e)}")
        except ConnectionError as e:
            self.logger.error(f"Connection error sending Telegram notification: {str(e)}")
        except ImportError as e:
            self.logger.error(f"Import error for Telegram dependencies: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {str(e)}")
            
    def send_trade_notification(self, message):
        """Send a trade-related notification with trade details."""
        self.send_notification(message)
        
    def send_order_notification(self, order):
        """Send notification with order details."""
        try:
            message = (
                f"🔄 Order Executed\n"
                f"Symbol: {order['symbol']}\n"
                f"Side: {order['side']}\n"
                f"Type: {order['type']}\n"
                f"Quantity: {order['executedQty']}\n"
                f"Price: {order.get('price', 'Market price')}"
            )
            self.send_notification(message)
        except KeyError as e:
            self.logger.error(f"Missing key in order data: {str(e)}")
        except TypeError as e:
            self.logger.error(f"Type error in order data: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Value error in order data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to send order notification: {str(e)}")
            
    def send_error_notification(self, error_message):
        """Send an error notification."""
        message = f"⚠️ Error: {error_message}"
        self.send_notification(message)
