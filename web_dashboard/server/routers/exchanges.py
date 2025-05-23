"""
Exchanges router module for the FastAPI server

This module contains routes for exchange connections and data:
- Exchange integration
- Balance data
- Supported exchanges
- API key management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Optional, Any
import logging
import numpy as np
from datetime import datetime, timedelta
import json

# Set up logger
logger = logging.getLogger('api_server')

# Create router
exchange_router = APIRouter(
    prefix="/exchanges",
    tags=["exchanges"]
)

@exchange_router.get("")
async def get_supported_exchanges():
    """Get list of supported exchanges"""
    try:
        return {
            "exchanges": [
                {
                    "id": "binance",
                    "name": "Binance",
                    "url": "https://www.binance.com",
                    "logo": "https://cdn.example.com/binance.png",
                    "hasFutures": True,
                    "hasFiat": True,
                    "supportsMarginTrading": True,
                    "supported": True
                },
                {
                    "id": "coinbase",
                    "name": "Coinbase Pro",
                    "url": "https://pro.coinbase.com",
                    "logo": "https://cdn.example.com/coinbase.png",
                    "hasFutures": False,
                    "hasFiat": True,
                    "supportsMarginTrading": False,
                    "supported": True
                },
                {
                    "id": "kraken",
                    "name": "Kraken",
                    "url": "https://www.kraken.com",
                    "logo": "https://cdn.example.com/kraken.png",
                    "hasFutures": True,
                    "hasFiat": True,
                    "supportsMarginTrading": True,
                    "supported": True
                },
                {
                    "id": "kucoin",
                    "name": "KuCoin",
                    "url": "https://www.kucoin.com",
                    "logo": "https://cdn.example.com/kucoin.png",
                    "hasFutures": True,
                    "hasFiat": True,
                    "supportsMarginTrading": True,
                    "supported": True
                },
                {
                    "id": "bybit",
                    "name": "Bybit",
                    "url": "https://www.bybit.com",
                    "logo": "https://cdn.example.com/bybit.png",
                    "hasFutures": True,
                    "hasFiat": True,
                    "supportsMarginTrading": True,
                    "supported": True
                }
            ]
        }
    except ValueError as e:
        logger.error(f"Value error in get_supported_exchanges: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid value: {str(e)}")
    except KeyError as e:
        logger.error(f"Missing key in exchange data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing exchange data: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"Exchange configuration file not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Exchange configuration not found")
    except PermissionError as e:
        logger.error(f"Permission error accessing exchange configuration: {str(e)}")
        raise HTTPException(status_code=403, detail="Permission denied accessing exchange configuration")
    except ConnectionError as e:
        logger.error(f"Connection error retrieving exchange data: {str(e)}")
        raise HTTPException(status_code=503, detail="Connection error with exchange service")
    except Exception as e:
        logger.error(f"Unexpected error in get_supported_exchanges: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@exchange_router.get("/user")
async def get_user_exchanges():
    """Get exchanges connected by the user"""
    try:
        return [
            {
                "id": "user-exchange-1",
                "exchangeId": "binance",
                "exchangeName": "Binance",
                "label": "My Binance Account",
                "isDemo": False,
                "connected": datetime.now().isoformat(),
                "lastSynced": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": "user-exchange-2",
                "exchangeId": "coinbase",
                "exchangeName": "Coinbase Pro",
                "label": "Coinbase Trading",
                "isDemo": False,
                "connected": (datetime.now() - timedelta(days=15)).isoformat(),
                "lastSynced": (datetime.now() - timedelta(hours=2)).isoformat(),
                "status": "active"
            },
            {
                "id": "user-exchange-3",
                "exchangeId": "bybit",
                "exchangeName": "Bybit",
                "label": "Bybit Futures",
                "isDemo": True,
                "connected": (datetime.now() - timedelta(days=5)).isoformat(),
                "lastSynced": (datetime.now() - timedelta(hours=4)).isoformat(),
                "status": "active"
            }
        ]
    except Exception as e:
        logger.error(f"Error in get_user_exchanges: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@exchange_router.get("/{exchange_id}/balances")
async def get_exchange_balances(exchange_id: str):
    """Get balances for a specific exchange"""
    try:
        # Mock different balances based on exchange
        balances = {}
        prices = {}
        
        if "binance" in exchange_id.lower():
            balances = {
                "BTC": "0.75",
                "ETH": "12.5",
                "USDT": "15000",
                "BNB": "25",
                "SOL": "100",
                "ADA": "2000",
            }
            
            prices = {
                "BTC": 42000,
                "ETH": 2800,
                "USDT": 1.0,
                "BNB": 350,
                "SOL": 140,
                "ADA": 0.55,
            }
        elif "coinbase" in exchange_id.lower():
            balances = {
                "BTC": "0.25",
                "ETH": "5.0",
                "USDC": "10000",
                "LINK": "500",
                "ATOM": "100",
            }
            
            prices = {
                "BTC": 42000,
                "ETH": 2800,
                "USDC": 1.0,
                "LINK": 15,
                "ATOM": 12,
            }
        else:
            balances = {
                "BTC": "0.1",
                "ETH": "3.0",
                "USDT": "5000",
            }
            
            prices = {
                "BTC": 42000,
                "ETH": 2800,
                "USDT": 1.0,
            }
        
        # Add daily changes
        changes = {key: round(np.random.uniform(-10, 10), 2) for key in balances.keys()}
        
        return {
            "exchange": exchange_id,
            "timestamp": datetime.now().isoformat(),
            "balances": balances,
            "prices": prices,
            "changes": changes
        }
    except Exception as e:
        logger.error(f"Error in get_exchange_balances: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@exchange_router.get("/{exchange_id}/market-data")
async def get_exchange_market_data(exchange_id: str, symbol: Optional[str] = None):
    """Get market data for a specific exchange"""
    try:
        # Mock market data
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "BNBUSDT"]
        if symbol:
            symbols = [s for s in symbols if s.lower() == symbol.lower()]
            
        result = []
        
        for sym in symbols:
            # Base price depends on the symbol
            if "BTC" in sym:
                base_price = 42000
                daily_volume = 1500000000
            elif "ETH" in sym:
                base_price = 2800
                daily_volume = 800000000
            elif "BNB" in sym:
                base_price = 350
                daily_volume = 300000000
            elif "SOL" in sym:
                base_price = 140
                daily_volume = 250000000
            else:
                base_price = 0.55
                daily_volume = 150000000
            
            # Add some variance
            price = round(base_price * (1 + np.random.uniform(-0.05, 0.05)), 2)
            
            result.append({
                "symbol": sym,
                "price": price,
                "volume24h": int(daily_volume * (1 + np.random.uniform(-0.2, 0.2))),
                "change24h": round(np.random.uniform(-5, 5), 2),
                "high24h": round(price * (1 + np.random.uniform(0.01, 0.05)), 2),
                "low24h": round(price * (1 - np.random.uniform(0.01, 0.05)), 2),
                "bid": round(price * 0.999, 2),
                "ask": round(price * 1.001, 2),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "exchange": exchange_id,
            "data": result[0] if symbol else result
        }
    except Exception as e:
        logger.error(f"Error in get_exchange_market_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@exchange_router.post("/{exchange_id}/orders")
async def place_order(
    exchange_id: str,
    order: Dict[str, Any] = Body(...)
):
    """Place an order on an exchange"""
    try:
        # Validate required fields
        required_fields = ["symbol", "side", "type", "quantity"]
        for field in required_fields:
            if field not in order:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate mock order ID and timestamp
        order_id = f"ord-{int(datetime.now().timestamp())}"
        timestamp = datetime.now().isoformat()
        
        # Extract order details
        symbol = order["symbol"]
        side = order["side"]
        order_type = order["type"]
        quantity = float(order["quantity"])
        
        # Get price for market orders or use provided price
        price = float(order.get("price", 0))
        if order_type.lower() == "market" or not price:
            # Mock market price based on symbol
            if "BTC" in symbol:
                price = round(np.random.uniform(41000, 43000), 2)
            elif "ETH" in symbol:
                price = round(np.random.uniform(2700, 2900), 2)
            else:
                price = round(np.random.uniform(100, 200), 2)
        
        # Create order response
        response = {
            "id": order_id,
            "exchange": exchange_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "status": "FILLED" if order_type.lower() == "market" else "NEW",
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        # Add filled details for market orders
        if order_type.lower() == "market":
            response["filled_quantity"] = quantity
            response["filled_price"] = price
            response["filled_at"] = timestamp
            
        return response
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Error in place_order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@exchange_router.get("/{exchange_id}/orders")
async def get_exchange_orders(
    exchange_id: str, 
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get orders for a specific exchange"""
    try:
        # Mock orders
        orders = []
        
        for i in range(limit):
            # Generate random time in the past
            created_hours_ago = np.random.randint(1, 72)
            created_at = datetime.now() - timedelta(hours=created_hours_ago)
            
            # Determine symbol if not specified
            order_symbol = symbol if symbol else np.random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
            
            # Determine status if not specified
            if status:
                order_status = status.upper()
            else:
                order_status = np.random.choice(["FILLED", "NEW", "CANCELED", "REJECTED"], p=[0.7, 0.2, 0.08, 0.02])
            
            # Generate price based on symbol
            if "BTC" in order_symbol:
                price = round(np.random.uniform(40000, 44000), 2)
            elif "ETH" in order_symbol:
                price = round(np.random.uniform(2700, 2900), 2)
            else:
                price = round(np.random.uniform(130, 150), 2)
            
            # Create order
            order = {
                "id": f"ord-{i}",
                "exchange": exchange_id,
                "symbol": order_symbol,
                "side": "BUY" if np.random.random() > 0.5 else "SELL",
                "type": np.random.choice(["MARKET", "LIMIT"]),
                "quantity": round(np.random.uniform(0.01, 1.0), 4),
                "price": price,
                "status": order_status,
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(minutes=np.random.randint(1, 60))).isoformat()
            }
            
            # Add filled details for FILLED orders
            if order["status"] == "FILLED":
                order["filled_quantity"] = order["quantity"]
                order["filled_price"] = price * (1 + np.random.uniform(-0.001, 0.001))
                order["filled_at"] = (created_at + timedelta(minutes=np.random.randint(1, 10))).isoformat()
            
            orders.append(order)
        
        return {"orders": orders}
    except Exception as e:
        logger.error(f"Error in get_exchange_orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
exchange_router = exchange_router
