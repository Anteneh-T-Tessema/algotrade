"""
Trading router module for the FastAPI server

This module contains routes for trading-related endpoints including:
- Strategy management
- Trading history
- Order execution
- Market data
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
import logging
import numpy as np
from datetime import datetime, timedelta

# Set up logger
logger = logging.getLogger('api_server')

# Create router
trading_router = APIRouter(
    prefix="/trading",
    tags=["trading"]
)

# Trading strategy endpoints

@trading_router.get("/strategies")
async def get_all_strategies():
    """Get all available trading strategies"""
    try:
        return {
            "strategies": [
                {
                    "id": "scalping",
                    "name": "Scalping Strategy",
                    "description": "Short-term strategy that aims to profit from small price changes",
                    "defaultParams": {
                        "timeframe": "5m",
                        "profitTarget": 1.5,
                        "stopLoss": 1.0,
                        "maxPositions": 3
                    },
                    "riskLevel": "high",
                    "suitableMarkets": ["normal", "trending"]
                },
                {
                    "id": "dca",
                    "name": "Dollar-Cost Averaging",
                    "description": "Investing a fixed amount at regular intervals regardless of price to reduce impact of volatility",
                    "defaultParams": {
                        "interval_hours": 24,
                        "buy_amount": 100,
                        "dip_threshold_pct": 5.0,
                        "take_profit_pct": 20.0
                    },
                    "riskLevel": "low",
                    "suitableMarkets": ["all"]
                },
                {
                    "id": "mean_reversion",
                    "name": "Mean Reversion",
                    "description": "Strategy based on the assumption that prices will revert to average over time",
                    "defaultParams": {
                        "lookback_period": 20,
                        "entry_threshold": 2.0,
                        "exit_threshold": 0.5
                    },
                    "riskLevel": "medium",
                    "suitableMarkets": ["sideways", "volatile"]
                },
                {
                    "id": "trend_following",
                    "name": "Trend Following",
                    "description": "Strategy that follows market trends, buying in uptrends and selling in downtrends",
                    "defaultParams": {
                        "fast_period": 12,
                        "slow_period": 26,
                        "signal_period": 9
                    },
                    "riskLevel": "medium",
                    "suitableMarkets": ["trending"]
                },
                {
                    "id": "grid_trading",
                    "name": "Grid Trading",
                    "description": "Places buy and sell orders at predefined intervals to profit from price oscillations",
                    "defaultParams": {
                        "upper_price": 45000,
                        "lower_price": 35000,
                        "num_grids": 10,
                        "quantity_per_grid": 0.01
                    },
                    "riskLevel": "medium",
                    "suitableMarkets": ["sideways", "volatile"]
                },
                {
                    "id": "arbitrage",
                    "name": "Arbitrage",
                    "description": "Profits from price differences between different exchanges",
                    "defaultParams": {
                        "min_profit_pct": 0.5,
                        "max_trade_size": 1000
                    },
                    "riskLevel": "low",
                    "suitableMarkets": ["all"]
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_all_strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@trading_router.get("/user-strategies")
async def get_user_strategies():
    """Get strategies created by the user"""
    try:
        return {
            "strategies": [
                {
                    "id": "user-strategy-1",
                    "name": "My Bitcoin DCA",
                    "baseStrategyId": "dca",
                    "symbol": "BTCUSDT",
                    "exchange": "binance",
                    "status": "active",
                    "created": "2025-02-15T10:30:00Z",
                    "lastModified": "2025-04-20T14:30:00Z",
                    "params": {
                        "interval_hours": 24,
                        "buy_amount": 250,
                        "dip_threshold_pct": 7.0,
                        "take_profit_pct": 25.0
                    },
                    "performance": {
                        "totalReturn": 12.5,
                        "avgEntryPrice": 38500,
                        "currentPrice": 43300
                    }
                },
                {
                    "id": "user-strategy-2",
                    "name": "ETH Grid",
                    "baseStrategyId": "grid_trading",
                    "symbol": "ETHUSDT",
                    "exchange": "binance",
                    "status": "paused",
                    "created": "2025-03-10T15:45:00Z",
                    "lastModified": "2025-04-15T09:30:00Z",
                    "params": {
                        "upper_price": 4000,
                        "lower_price": 3000,
                        "num_grids": 8,
                        "quantity_per_grid": 0.05
                    },
                    "performance": {
                        "totalReturn": 8.2,
                        "tradesExecuted": 24,
                        "profitableTrades": 18
                    }
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_user_strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@trading_router.get("/orderbook")
async def get_orderbook_data(symbol: str = "BTCUSDT", depth: int = 10):
    """Get order book data for a trading pair"""
    try:
        # Mock orderbook data
        asks = [[round(40000 + i * 10 + np.random.normal(0, 2), 2), round(np.random.uniform(0.1, 2.0), 4)] for i in range(depth)]
        bids = [[round(39990 - i * 10 + np.random.normal(0, 2), 2), round(np.random.uniform(0.1, 2.0), 4)] for i in range(depth)]
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "asks": asks,
            "bids": bids
        }
    except Exception as e:
        logger.error(f"Error in get_orderbook_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@trading_router.get("/recent-trades")
async def get_recent_trades(symbol: str = "BTCUSDT", limit: int = 50):
    """Get recent trades for a symbol"""
    try:
        # Mock recent trades
        trades = []
        base_price = 40000
        
        for i in range(limit):
            price = round(base_price + np.random.normal(0, 100), 2)
            amount = round(np.random.uniform(0.001, 0.1), 6)
            side = "buy" if np.random.random() > 0.5 else "sell"
            timestamp = datetime.now() - timedelta(seconds=i * 15)
            
            trades.append({
                "id": f"t{i}",
                "price": price,
                "amount": amount,
                "side": side,
                "timestamp": timestamp.isoformat()
            })
        
        return {
            "symbol": symbol,
            "trades": trades
        }
    except Exception as e:
        logger.error(f"Error in get_recent_trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@trading_router.get("/history")
async def get_trading_history(
    symbol: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get trading history with optional filters"""
    try:
        # Mock trade history
        history = []
        
        for i in range(offset, offset + limit):
            days_ago = np.random.randint(1, 60)
            entry_date = datetime.now() - timedelta(days=days_ago)
            exit_date = entry_date + timedelta(hours=np.random.randint(1, 168))
            
            # Skip if outside specified date range
            if startDate and entry_date < datetime.fromisoformat(startDate):
                continue
            if endDate and exit_date > datetime.fromisoformat(endDate):
                continue
            
            # Choose a random symbol if not specified
            trade_symbol = symbol if symbol else np.random.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"])
            
            # Base prices on the symbol
            if trade_symbol == "BTCUSDT":
                entry_price = round(np.random.uniform(35000, 45000), 2)
            elif trade_symbol == "ETHUSDT":
                entry_price = round(np.random.uniform(2000, 3500), 2)
            elif trade_symbol == "SOLUSDT":
                entry_price = round(np.random.uniform(100, 200), 2)
            else:
                entry_price = round(np.random.uniform(0.3, 0.7), 3)
            
            # Generate exit price with some profit/loss
            change_pct = np.random.normal(0.02, 0.10)  # Mean 2% gain with standard deviation of 10%
            exit_price = round(entry_price * (1 + change_pct), 2)
            
            # Calculate profit in quote currency and percentage
            size = round(np.random.uniform(0.01, 1.0), 6)
            profit_amount = round((exit_price - entry_price) * size, 2)
            profit_percentage = round(change_pct * 100, 2)
            
            history.append({
                "id": f"trade-{i}",
                "symbol": trade_symbol,
                "side": "BUY",
                "size": size,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_time": entry_date.isoformat(),
                "exit_time": exit_date.isoformat(),
                "profit_amount": profit_amount,
                "profit_percentage": profit_percentage,
                "strategy": np.random.choice(["DCA", "Grid Trading", "Trend Following"]),
                "status": "CLOSED"
            })
        
        return {
            "history": sorted(history, key=lambda x: x["entry_time"], reverse=True),
            "total": 230,  # Mock total for pagination
            "has_more": (offset + limit) < 230
        }
    except Exception as e:
        logger.error(f"Error in get_trading_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@trading_router.get("/dashboard")
async def get_dashboard_data(period: str = "24h"):
    """Get data for the main dashboard"""
    try:
        # Mock dashboard data
        current_time = datetime.now()
        
        # Generate hourly price data for last 24 hours
        price_data = []
        base_price = 40000
        for i in range(24):
            time_point = current_time - timedelta(hours=23-i)
            price = base_price * (1 + np.random.normal(0.0005, 0.008) * i)
            price_data.append({
                "time": time_point.strftime('%Y-%m-%d %H:%M'),
                "price": round(price, 2)
            })
            base_price = price
        
        return {
            "balance": {
                "total": round(np.random.uniform(50000, 200000), 2),
                "change24h": round(np.random.uniform(-5, 10), 2),
                "fiat": round(np.random.uniform(10000, 30000), 2),
                "crypto": round(np.random.uniform(40000, 170000), 2),
            },
            "activeStrategies": np.random.randint(1, 5),
            "totalTrades": np.random.randint(50, 500),
            "profitableTrades": np.random.randint(30, 350),
            "recentActivity": [
                {
                    "time": (current_time - timedelta(minutes=np.random.randint(5, 60))).strftime('%H:%M'),
                    "event": "Trade executed",
                    "details": "Bought 0.015 BTC at $41,235"
                },
                {
                    "time": (current_time - timedelta(hours=np.random.randint(1, 5))).strftime('%H:%M'),
                    "event": "Strategy started",
                    "details": "DCA strategy for ETH activated"
                },
                {
                    "time": (current_time - timedelta(hours=np.random.randint(6, 12))).strftime('%H:%M'),
                    "event": "Take profit hit",
                    "details": "Sold 0.5 SOL at $154.25 (+12.3%)"
                },
            ],
            "priceData": price_data,
            "topPerformers": [
                {"symbol": "BTC", "change": round(np.random.uniform(-5, 15), 2)},
                {"symbol": "ETH", "change": round(np.random.uniform(-5, 15), 2)},
                {"symbol": "SOL", "change": round(np.random.uniform(-5, 15), 2)}
            ],
            "worstPerformers": [
                {"symbol": "DOGE", "change": round(np.random.uniform(-15, -1), 2)},
                {"symbol": "XRP", "change": round(np.random.uniform(-15, -1), 2)},
                {"symbol": "ADA", "change": round(np.random.uniform(-15, -1), 2)}
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_dashboard_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
# The trading_router variable is already defined at the top of the file
# Remove the reassignment that's causing confusion
# 