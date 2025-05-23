#!/usr/bin/env python3
"""
FastAPI Server for Trading Platform

This module provides the REST API backend for the crypto trading platform web dashboard.
It implements endpoints for strategy management, market data, portfolio tracking,
and multi-tier distribution system.
"""

import os
import sys
import logging
import json
import random
import time
import asyncio  # Make sure asyncio is imported
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import project modules
from strategies.base_strategy import Strategy
from utils.history_loader import HistoryLoader
from utils.logger import setup_logger

# Set up logger
# Create a basic logger if the setup_logger function requires a log file
try:
    logger = setup_logger('api_server', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'api_server.log'))
except TypeError:
    # If setup_logger requires a log_file but we can't provide one, use a basic logger
    logger = logging.getLogger('api_server')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Create FastAPI app
app = FastAPI(
    title="Crypto Trading Platform API",
    description="REST API for algorithmic crypto trading platform",
    version="1.0.0"
)

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include all API routers
from .routers import api_router
app.include_router(api_router, prefix="/v1")

# WebSocket connection manager for real-time data
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, data_type: str):
        await websocket.accept()
        if data_type not in self.active_connections:
            self.active_connections[data_type] = []
        self.active_connections[data_type].append((client_id, websocket))
        logger.info(f"Client {client_id} connected for {data_type} data. Total connections for {data_type}: {len(self.active_connections[data_type])}")

    def disconnect(self, websocket: WebSocket, client_id: str, data_type: str):
        if data_type in self.active_connections:
            self.active_connections[data_type] = [(cid, ws) for cid, ws in self.active_connections[data_type] if cid != client_id]
            logger.info(f"Client {client_id} disconnected from {data_type} data. Total connections for {data_type}: {len(self.active_connections[data_type])}")

    async def broadcast(self, data_type: str, message: dict):
        if data_type in self.active_connections:
            disconnected = []
            for client_id, connection in self.active_connections[data_type]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to client {client_id}: {str(e)}")
                    disconnected.append((client_id, connection))
            
            # Clean up disconnected clients
            for client_id, connection in disconnected:
                self.disconnect(connection, client_id, data_type)

manager = ConnectionManager()

# Define background tasks for real-time data updates
async def market_data_background_task():
    """Background task to periodically broadcast market data updates"""
    while True:
        try:
            # Get latest market data
            # In a real implementation, this would fetch from exchanges or database
            data = {
                "type": "market_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "BTC": {"price": round(35000 + np.random.normal(0, 300), 2), "change24h": round(np.random.normal(0, 1.5), 2)},
                    "ETH": {"price": round(2500 + np.random.normal(0, 100), 2), "change24h": round(np.random.normal(0, 2.0), 2)},
                    "SOL": {"price": round(150 + np.random.normal(0, 5), 2), "change24h": round(np.random.normal(0, 3.0), 2)},
                    "DOGE": {"price": round(0.12 + np.random.normal(0, 0.01), 4), "change24h": round(np.random.normal(0, 2.5), 2)},
                }
            }
            
            # Broadcast to subscribers
            await manager.broadcast("market", data)
            
        except Exception as e:
            logger.error(f"Error in market data background task: {str(e)}")
        
        # Wait before the next update
        await asyncio.sleep(5)  # Update every 5 seconds

async def orderbook_background_task():
    """Background task to periodically broadcast orderbook updates"""
    while True:
        try:
            # Generate mock orderbook data
            asks = [[round(40000 + i * 10 + np.random.normal(0, 2), 2), round(np.random.uniform(0.1, 2.0), 4)] for i in range(10)]
            bids = [[round(39990 - i * 10 + np.random.normal(0, 2), 2), round(np.random.uniform(0.1, 2.0), 4)] for i in range(10)]
            
            data = {
                "type": "orderbook_update",
                "symbol": "BTCUSDT",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "asks": asks,
                    "bids": bids
                }
            }
            
            # Broadcast to subscribers
            await manager.broadcast("orderbook", data)
            
        except Exception as e:
            logger.error(f"Error in orderbook background task: {str(e)}")
        
        # Wait before the next update
        await asyncio.sleep(2)  # Update every 2 seconds

async def portfolio_background_task():
    """Background task to periodically broadcast portfolio updates"""
    while True:
        try:
            # In a real implementation, this would query user portfolio data
            # For now, generate simulated portfolio data
            btc_price = 40000 + np.random.normal(0, 200)
            eth_price = 2800 + np.random.normal(0, 50)
            sol_price = 150 + np.random.normal(0, 5)
            
            btc_amount = 0.75
            eth_amount = 8.5
            sol_amount = 32.5
            
            btc_value = btc_price * btc_amount
            eth_value = eth_price * eth_amount
            sol_value = sol_price * sol_amount
            total_value = btc_value + eth_value + sol_value
            
            # Calculate daily changes (simulated)
            btc_change = round(np.random.uniform(-2, 2), 2)
            eth_change = round(np.random.uniform(-2, 2), 2)
            sol_change = round(np.random.uniform(-4, 4), 2)
            
            # Calculate weighted average change
            daily_change = (btc_change * btc_value + eth_change * eth_value + sol_change * sol_value) / total_value
            
            portfolio_data = {
                "type": "portfolio_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_value": round(total_value, 2),
                    "daily_change": round(daily_change, 2),
                    "assets": [
                        {"symbol": "BTC", "amount": btc_amount, "value_usd": round(btc_value, 2), "change24h": btc_change},
                        {"symbol": "ETH", "amount": eth_amount, "value_usd": round(eth_value, 2), "change24h": eth_change},
                        {"symbol": "SOL", "amount": sol_amount, "value_usd": round(sol_value, 2), "change24h": sol_change}
                    ]
                }
            }
            
            # Broadcast to subscribers
            await manager.broadcast("portfolio", portfolio_data)
            
        except Exception as e:
            logger.error(f"Error in portfolio background task: {str(e)}")
        
        # Wait before the next update
        await asyncio.sleep(10)  # Update every 10 seconds

async def trades_background_task():
    """Background task to periodically broadcast trade updates"""
    while True:
        try:
            # Wait a random interval before generating a new trade
            await asyncio.sleep(random.uniform(5, 20))
            
            # Generate a random trade
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
            sides = ["buy", "sell"]
            
            symbol = random.choice(symbols)
            side = random.choice(sides)
            
            # Set price based on symbol
            if symbol == "BTCUSDT":
                price = round(40000 + np.random.normal(0, 200), 2)
                amount = round(random.uniform(0.01, 0.5), 4)
            elif symbol == "ETHUSDT":
                price = round(2800 + np.random.normal(0, 50), 2)
                amount = round(random.uniform(0.1, 5), 3)
            elif symbol == "SOLUSDT":
                price = round(150 + np.random.normal(0, 5), 2)
                amount = round(random.uniform(1, 20), 2)
            else:  # DOGEUSDT
                price = round(0.12 + np.random.normal(0, 0.005), 4)
                amount = round(random.uniform(100, 10000), 0)
            
            trade_data = {
                "type": "trade_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "id": f"t{int(time.time() * 1000)}",
                    "symbol": symbol,
                    "side": side,
                    "price": price,
                    "amount": amount,
                    "time": datetime.now().isoformat(),
                    "value": round(price * amount, 2)
                }
            }
            
            # Broadcast to subscribers
            await manager.broadcast("trades", trade_data)
            
        except Exception as e:
            logger.error(f"Error in trades background task: {str(e)}")

# Start background tasks
@app.on_event("startup")
async def startup_event():
    logger.info("Starting background tasks")
    asyncio.create_task(market_data_background_task())
    asyncio.create_task(orderbook_background_task())
    asyncio.create_task(portfolio_background_task())
    asyncio.create_task(trades_background_task())

# WebSocket endpoints for real-time data
@app.websocket("/v1/ws/market/{client_id}")
async def websocket_market_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id, "market")
    crypto_data = {
        "BTC": {"name": "Bitcoin", "price": 58750.25, "change24h": 1.2, "marketCap": 1.15e12, "volume24h": 32.5e9},
        "ETH": {"name": "Ethereum", "price": 3845.75, "change24h": -0.8, "marketCap": 4.62e11, "volume24h": 18.7e9},
        "SOL": {"name": "Solana", "price": 153.42, "change24h": 3.5, "marketCap": 6.52e10, "volume24h": 4.2e9},
        "DOGE": {"name": "Dogecoin", "price": 0.122, "change24h": -2.1, "marketCap": 1.62e10, "volume24h": 1.8e9},
        "BNB": {"name": "Binance Coin", "price": 585.32, "change24h": 0.7, "marketCap": 8.9e10, "volume24h": 2.1e9},
        "XRP": {"name": "Ripple", "price": 0.64, "change24h": -1.5, "marketCap": 3.35e10, "volume24h": 1.5e9},
        "ADA": {"name": "Cardano", "price": 0.48, "change24h": 2.3, "marketCap": 1.71e10, "volume24h": 728e6},
        "DOT": {"name": "Polkadot", "price": 7.82, "change24h": -0.4, "marketCap": 9.82e9, "volume24h": 325e6},
        "AVAX": {"name": "Avalanche", "price": 34.65, "change24h": 5.2, "marketCap": 1.28e10, "volume24h": 512e6},
        "MATIC": {"name": "Polygon", "price": 0.68, "change24h": 2.8, "marketCap": 6.72e9, "volume24h": 428e6},
    }
    
    try:
        # Send initial data immediately upon connection
        market_data = {
            "type": "market_update",
            "timestamp": datetime.now().isoformat(),
            "data": crypto_data
        }
        await websocket.send_json(market_data)
        
        # Simulate real-time market data updates
        update_counter = 0
        while True:
            # Wait a bit between updates
            await asyncio.sleep(3)
            
            update_counter += 1
            
            # Choose which cryptocurrencies to update (not all on every update)
            symbols_to_update = random.sample(list(crypto_data.keys()), k=min(3, len(crypto_data)))
            
            # Update prices with small variations
            for symbol in symbols_to_update:
                # Generate price change (more volatile for lower-cap coins)
                coin_data = crypto_data[symbol]
                volatility = 0.002 if coin_data["marketCap"] > 1e11 else 0.005
                price_change = coin_data["price"] * random.uniform(-volatility, volatility)
                
                # Update price
                new_price = max(0.00001, coin_data["price"] + price_change)
                
                # Update 24h change (slowly drift)
                new_change = coin_data["change24h"] + random.uniform(-0.2, 0.2)
                # Keep change within reasonable bounds
                new_change = max(-15, min(15, new_change))
                
                # Update volume (random small changes)
                volume_change = coin_data["volume24h"] * random.uniform(-0.01, 0.01)
                new_volume = max(1000, coin_data["volume24h"] + volume_change)
                
                # Store updated values
                crypto_data[symbol]["price"] = new_price
                crypto_data[symbol]["change24h"] = new_change
                crypto_data[symbol]["volume24h"] = new_volume
            
            # Send update with only the changed coins
            update_data = {symbol: crypto_data[symbol] for symbol in symbols_to_update}
            await websocket.send_json({
                "type": "market_update",
                "timestamp": datetime.now().isoformat(),
                "data": update_data
            })
            
            # Every 10 updates, send heartbeat to check connection
            if update_counter % 10 == 0:
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait for any messages from the client (non-blocking)
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                # Handle subscription updates if needed
                if data.get("action") == "subscribe" and "symbols" in data:
                    logger.info(f"Client {client_id} subscribed to symbols: {data['symbols']}")
            except asyncio.TimeoutError:
                # No message from client, continue with updates
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, "market")
        logger.info(f"Client {client_id} disconnected from market data")
    except Exception as e:
        logger.error(f"Error in market WebSocket: {str(e)}")
        manager.disconnect(websocket, client_id, "market")

@app.websocket("/v1/ws/orderbook/{client_id}")
async def websocket_orderbook_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id, "orderbook")
    try:
        # Send initial orderbook data upon connection
        asks = [[40010.25, 1.2], [40020.50, 0.8], [40030.75, 2.5], [40040.00, 1.1], [40050.25, 3.2]]
        bids = [[39990.75, 1.5], [39980.50, 2.2], [39970.25, 1.8], [39960.00, 0.9], [39950.50, 2.7]]
        
        initial_data = {
            "type": "orderbook_snapshot",
            "symbol": "BTCUSDT",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "asks": asks,
                "bids": bids
            }
        }
        await websocket.send_json(initial_data)
        
        while True:
            # Wait for any messages from the client
            data = await websocket.receive_json()
            # Handle symbol changes if needed
            if data.get("action") == "change_symbol" and "symbol" in data:
                logger.info(f"Client {client_id} changed orderbook symbol to: {data['symbol']}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, "orderbook")
    except Exception as e:
        logger.error(f"Error in orderbook WebSocket: {str(e)}")
        manager.disconnect(websocket, client_id, "orderbook")

@app.websocket("/v1/ws/portfolio/{client_id}")
async def websocket_portfolio_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id, "portfolio")
    try:
        # Send initial portfolio data upon connection
        portfolio_data = {
            "type": "portfolio_update",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "total_value": 58432.75,
                "daily_change": 2.3,
                "assets": [
                    {"symbol": "BTC", "amount": 0.75, "value_usd": 29062.68, "change24h": 1.2},
                    {"symbol": "ETH", "amount": 8.5, "value_usd": 24188.87, "change24h": -0.8},
                    {"symbol": "SOL", "amount": 32.5, "value_usd": 4986.15, "change24h": 3.5}
                ]
            }
        }
        await websocket.send_json(portfolio_data)
        
        while True:
            # Wait for any messages from the client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, "portfolio")
    except Exception as e:
        logger.error(f"Error in portfolio WebSocket: {str(e)}")
        manager.disconnect(websocket, client_id, "portfolio")

@app.websocket("/v1/ws/trades/{client_id}")
async def websocket_trades_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id, "trades")
    try:
        # Send initial trades data upon connection
        trades_data = {
            "type": "trades_update",
            "timestamp": datetime.now().isoformat(),
            "data": [
                {"id": "t123456", "symbol": "BTCUSDT", "side": "buy", "price": 39875.50, "amount": 0.05, "time": (datetime.now() - timedelta(minutes=5)).isoformat()},
                {"id": "t123457", "symbol": "ETHUSDT", "side": "sell", "price": 2830.25, "amount": 1.2, "time": (datetime.now() - timedelta(minutes=12)).isoformat()},
                {"id": "t123458", "symbol": "SOLUSDT", "side": "buy", "price": 148.75, "amount": 10.0, "time": (datetime.now() - timedelta(minutes=18)).isoformat()}
            ]
        }
        await websocket.send_json(trades_data)
        
        while True:
            # Wait for any messages from the client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, "trades")
    except Exception as e:
        logger.error(f"Error in trades WebSocket: {str(e)}")
        manager.disconnect(websocket, client_id, "trades")

# Model definitions for API requests and responses
class MarketDataResponse(BaseModel):
    cryptocurrencies: List[Dict[str, Any]]

class PortfolioSummaryResponse(BaseModel):
    total_value: float
    daily_change: float
    assets: List[Dict[str, Any]]

class DistributorCommissionResponse(BaseModel):
    total_earnings: float
    period_earnings: float
    commissions: List[Dict[str, Any]]
    network: Dict[str, Any]

# API Endpoints

# Market Data Endpoints
@app.get("/trading/market-data", response_model=MarketDataResponse)
async def get_market_data(
    limit: int = 100, 
    sortBy: str = "marketCap", 
    order: str = "desc"
):
    """Get cryptocurrency market data"""
    try:
        # Mock data generation for now
        # In a real implementation, this would query APIs or database
        mock_data = []
        for i in range(1, limit + 1):
            price = round(np.random.uniform(10, 50000), 2) if i > 20 else round(np.random.uniform(1000, 50000), 2)
            change = round(np.random.uniform(-10, 10), 2)
            market_cap = price * round(np.random.uniform(1000000, 100000000))
            
            # Generate sparkline data
            sparkline_data = []
            current = price * 0.9
            for _ in range(7):
                current = current * (1 + np.random.uniform(-0.02, 0.02))
                sparkline_data.append({"value": round(current, 2)})
            
            mock_data.append({
                "id": f"crypto{i}",
                "name": f"Crypto {i}",
                "symbol": f"C{i}",
                "image": f"https://example.com/crypto{i}.png",
                "currentPrice": price,
                "marketCap": market_cap,
                "marketCapRank": i,
                "totalVolume": market_cap * np.random.uniform(0.05, 0.15),
                "priceChange24h": change,
                "sparklineData": sparkline_data
            })
        
        # Sort data
        reverse = order.lower() == "desc"
        sorted_data = sorted(mock_data, key=lambda x: x.get(sortBy, 0), reverse=reverse)
        
        return {"cryptocurrencies": sorted_data}
    except Exception as e:
        logger.error(f"Error in get_market_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/chart-data")
async def get_chart_data(
    symbol: str, 
    timeframe: str = "1h",
    from_time: Optional[int] = None,
    to_time: Optional[int] = None
):
    """Get OHLCV data for charting"""
    try:
        # Mock data generation
        # In a real implementation, this would query exchange APIs or database
        now = datetime.now().timestamp()
        from_timestamp = from_time if from_time else int(now - 7 * 24 * 3600)
        to_timestamp = to_time if to_time else int(now)
        
        # Determine candle duration based on timeframe
        if timeframe == "1m":
            seconds_per_candle = 60
        elif timeframe == "5m":
            seconds_per_candle = 300
        elif timeframe == "15m":
            seconds_per_candle = 900
        elif timeframe == "1h":
            seconds_per_candle = 3600
        elif timeframe == "4h":
            seconds_per_candle = 14400
        elif timeframe == "1d":
            seconds_per_candle = 86400
        else:
            seconds_per_candle = 3600  # Default to 1h
        
        # Generate OHLCV data
        data = []
        timestamp = from_timestamp
        last_close = 40000.0  # Starting price for BTC example
        
        while timestamp < to_timestamp:
            # Generate realistic looking price action
            open_price = last_close
            high = open_price * (1 + np.random.uniform(0, 0.02))
            low = open_price * (1 - np.random.uniform(0, 0.02))
            close = open_price * (1 + np.random.normal(0, 0.008))
            volume = np.random.uniform(10, 100) * abs(close - open_price) * 100
            
            data.append({
                "time": timestamp,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": round(volume, 2)
            })
            
            last_close = close
            timestamp += seconds_per_candle
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error in get_chart_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/technical-indicators")
async def get_technical_indicators(
    symbol: str,
    timeframe: str = "1d",
    indicators: str = "sma,ema,rsi"
):
    """Get technical indicators for a symbol"""
    try:
        # Parse requested indicators
        indicator_list = indicators.split(',')
        
        # Get chart data first (reuse the function)
        chart_data = await get_chart_data(symbol, timeframe)
        
        # Convert to DataFrame for indicator calculation
        df = pd.DataFrame(chart_data["data"])
        
        # Calculate indicators
        results = {}
        
        if 'sma' in indicator_list:
            # Simple Moving Average
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['sma200'] = df['close'].rolling(window=200).mean()
            results["sma"] = {
                "sma20": df['sma20'].dropna().tolist(),
                "sma50": df['sma50'].dropna().tolist(),
                "sma200": df['sma200'].dropna().tolist(),
            }
        
        if 'ema' in indicator_list:
            # Exponential Moving Average
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            results["ema"] = {
                "ema12": df['ema12'].dropna().tolist(),
                "ema26": df['ema26'].dropna().tolist(),
            }
        
        if 'rsi' in indicator_list:
            # Relative Strength Index
            delta = df['close'].diff()
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / (avg_loss + 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            results["rsi"] = {
                "rsi14": df['rsi'].dropna().tolist(),
            }
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "indicators": results
        }
    except Exception as e:
        logger.error(f"Error in get_technical_indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Portfolio Endpoints
@app.get("/trading/portfolio/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary():
    """Get overall portfolio summary across all exchanges"""
    try:
        # Mock data
        total_value = round(np.random.uniform(50000, 200000), 2)
        daily_change = round(np.random.uniform(-5, 5), 2)
        
        assets = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "amount": round(np.random.uniform(0.5, 2.0), 8),
                "value": round(np.random.uniform(20000, 80000), 2),
                "allocationPct": round(np.random.uniform(20, 60), 2),
                "priceChangeDay": round(np.random.uniform(-7, 7), 2),
                "priceChangeWeek": round(np.random.uniform(-15, 15), 2),
            },
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "amount": round(np.random.uniform(5, 20), 8),
                "value": round(np.random.uniform(10000, 40000), 2),
                "allocationPct": round(np.random.uniform(10, 40), 2),
                "priceChangeDay": round(np.random.uniform(-10, 10), 2),
                "priceChangeWeek": round(np.random.uniform(-20, 20), 2),
            },
            {
                "symbol": "SOL",
                "name": "Solana",
                "amount": round(np.random.uniform(50, 200), 8),
                "value": round(np.random.uniform(5000, 20000), 2),
                "allocationPct": round(np.random.uniform(5, 20), 2),
                "priceChangeDay": round(np.random.uniform(-12, 12), 2),
                "priceChangeWeek": round(np.random.uniform(-25, 25), 2),
            },
            {
                "symbol": "USDT",
                "name": "Tether",
                "amount": round(np.random.uniform(5000, 20000), 2),
                "value": round(np.random.uniform(5000, 20000), 2),
                "allocationPct": round(np.random.uniform(5, 25), 2),
                "priceChangeDay": 0,
                "priceChangeWeek": 0,
            },
        ]
        
        return {
            "total_value": total_value,
            "daily_change": daily_change,
            "assets": assets
        }
    except Exception as e:
        logger.error(f"Error in get_portfolio_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/portfolio/performance")
async def get_portfolio_performance(period: str = "1month"):
    """Get portfolio performance over time"""
    try:
        # Define timeframe based on period
        days = 30  # Default to 1 month
        
        if period == "1week":
            days = 7
        elif period == "1month":
            days = 30
        elif period == "3months":
            days = 90
        elif period == "6months":
            days = 180
        elif period == "1year":
            days = 365
        elif period == "all":
            days = 730  # 2 years
        
        # Generate performance data
        now = datetime.now()
        performance_data = []
        portfolio_value = 100000  # Starting value
        
        for day in range(days):
            date = (now - timedelta(days=days-day)).strftime('%Y-%m-%d')
            
            # Generate realistic looking portfolio performance
            daily_change_pct = np.random.normal(0.001, 0.02)  # Slight upward bias with volatility
            portfolio_value *= (1 + daily_change_pct)
            
            performance_data.append({
                "date": date,
                "value": round(portfolio_value, 2),
                "change": round(daily_change_pct * 100, 2)
            })
        
        return {
            "period": period,
            "data": performance_data,
            "starting_value": round(performance_data[0]["value"], 2),
            "current_value": round(performance_data[-1]["value"], 2),
            "total_change_pct": round((performance_data[-1]["value"] / performance_data[0]["value"] - 1) * 100, 2),
        }
    except Exception as e:
        logger.error(f"Error in get_portfolio_performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Distributor Endpoints
@app.get("/distributor/commissions", response_model=DistributorCommissionResponse)
async def get_distributor_commissions(
    period: str = "1month",
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    tier: Optional[int] = None
):
    """Get commission data for the distributor network"""
    try:
        # Mock data
        total_earnings = round(np.random.uniform(5000, 20000), 2)
        period_earnings = round(np.random.uniform(1000, 5000), 2)
        
        # Generate commission data
        commissions = []
        for i in range(10):
            tier_level = (i % 3) + 1
            
            # Skip if specific tier requested and doesn't match
            if tier is not None and tier_level != tier:
                continue
                
            commission_amount = round(np.random.uniform(100, 1000), 2)
            commissions.append({
                "id": f"comm-{i}",
                "date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                "amount": commission_amount,
                "tier": tier_level,
                "source": f"User {10 + i}",
                "status": "Paid" if np.random.random() > 0.2 else "Pending"
            })
        
        # Generate network statistics
        network = {
            "totalMembers": np.random.randint(50, 200),
            "activeMembers": np.random.randint(30, 100),
            "tierDistribution": {
                "tier1": np.random.randint(20, 100),
                "tier2": np.random.randint(10, 50),
                "tier3": np.random.randint(5, 20),
            },
            "growthRate": round(np.random.uniform(2.0, 15.0), 1)
        }
        
        return {
            "total_earnings": total_earnings,
            "period_earnings": period_earnings,
            "commissions": commissions,
            "network": network
        }
    except Exception as e:
        logger.error(f"Error in get_distributor_commissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/distributor/network")
async def get_distributor_network(
    depth: int = 3,
    userId: Optional[str] = None
):
    """Get distributor network structure"""
    try:
        # Mock network data
        network_data = {
            "id": "user-1",
            "name": "John Doe",
            "tier": 3,
            "joinDate": "2024-01-15",
            "earnings": round(np.random.uniform(5000, 20000), 2),
            "children": []
        }
        
        # Generate network tree
        def generate_children(parent, current_depth, max_depth):
            if current_depth >= max_depth:
                return
                
            num_children = np.random.randint(2, 5)
            for i in range(num_children):
                child = {
                    "id": f"user-{np.random.randint(100, 999)}",
                    "name": f"User {np.random.randint(100, 999)}",
                    "tier": max(1, parent["tier"] - 1),
                    "joinDate": (datetime.now() - timedelta(days=np.random.randint(10, 300))).strftime('%Y-%m-%d'),
                    "earnings": round(np.random.uniform(500, 5000), 2),
                    "children": []
                }
                parent["children"].append(child)
                generate_children(child, current_depth + 1, max_depth)
        
        generate_children(network_data, 1, depth)
        
        return network_data
    except Exception as e:
        logger.error(f"Error in get_distributor_network: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/distributor/commission-tiers")
async def get_commission_tiers():
    """Get information about commission tier structure"""
    try:
        return {
            "tiers": [
                {
                    "id": 1,
                    "name": "Bronze",
                    "requirements": "1-5 direct referrals",
                    "commissionRate": 5.0,
                    "directBonusRate": 10.0,
                    "levels": 1
                },
                {
                    "id": 2,
                    "name": "Silver",
                    "requirements": "6-20 direct referrals or $5,000 group volume",
                    "commissionRate": 8.0,
                    "directBonusRate": 15.0,
                    "levels": 2
                },
                {
                    "id": 3,
                    "name": "Gold",
                    "requirements": "21+ direct referrals or $20,000 group volume",
                    "commissionRate": 10.0,
                    "directBonusRate": 20.0,
                    "levels": 3
                },
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_commission_tiers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Main executable
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
