"""
User settings router module for the FastAPI server

This module contains routes for managing user settings and preferences:
- Dashboard layout preferences
- Chart preferences
- Notification setti        logger.error(f"Error in save_notification_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) API key management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

# Set up logger
logger = logging.getLogger('api_server')

# Create router
settings_router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)

@settings_router.get("/dashboard-preferences")
async def get_dashboard_preferences():
    """Get user's dashboard preferences"""
    try:
        # Mock user preferences
        return {
            "layout": "2-column",
            "defaultTimeframe": "1D",
            "favoriteSymbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "defaultExchange": "binance",
            "widgetsOrder": [
                "portfolio-summary",
                "price-chart",
                "trading-history",
                "open-orders",
                "market-overview",
                "active-strategies"
            ],
            "theme": "dark",
            "hiddenWidgets": ["network-status"],
            "advanced": {
                "showTradingVolume": True,
                "autoRefresh": True,
                "refreshInterval": 30
            }
        }
    except KeyError as e:
        logger.error(f"Missing key in dashboard preferences: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing preference key: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid value in dashboard preferences: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid preference value: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"Preferences file not found: {str(e)}")
        raise HTTPException(status_code=404, detail="User preferences not found")
    except PermissionError as e:
        logger.error(f"Permission error accessing preferences: {str(e)}")
        raise HTTPException(status_code=403, detail="Permission denied accessing preferences")
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@settings_router.put("/dashboard-preferences")
async def update_dashboard_preferences(preferences: Dict[str, Any] = Body(...)):
    """Update user's dashboard preferences"""
    try:
        # In a real implementation, this would save to database
        # For now, just validate and return the updated preferences
        
        # Validate layout
        valid_layouts = ["1-column", "2-column", "3-column", "custom"]
        if "layout" in preferences and preferences["layout"] not in valid_layouts:
            raise HTTPException(status_code=400, detail=f"Invalid layout. Must be one of {valid_layouts}")
        
        # Validate theme
        valid_themes = ["light", "dark", "auto"]
        if "theme" in preferences and preferences["theme"] not in valid_themes:
            raise HTTPException(status_code=400, detail=f"Invalid theme. Must be one of {valid_themes}")
        
        return {
            "success": True,
            "message": "Dashboard preferences updated successfully",
            "updatedAt": datetime.now().isoformat(),
            "preferences": preferences
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in update_dashboard_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@settings_router.get("/chart-preferences")
async def get_chart_preferences():
    """Get user's chart preferences"""
    try:
        return {
            "defaultTimeframe": "1h",
            "defaultInterval": "candle",
            "indicators": [
                {
                    "name": "MA",
                    "parameters": {
                        "period": 20,
                        "type": "sma"
                    },
                    "visible": True
                },
                {
                    "name": "RSI",
                    "parameters": {
                        "period": 14,
                        "overbought": 70,
                        "oversold": 30
                    },
                    "visible": True
                },
                {
                    "name": "MACD",
                    "parameters": {
                        "fastPeriod": 12,
                        "slowPeriod": 26,
                        "signalPeriod": 9
                    },
                    "visible": False
                }
            ],
            "showVolume": True,
            "showGrid": True,
            "chartStyle": "candles",
            "colorScheme": {
                "background": "#121212",
                "text": "#e0e0e0",
                "grid": "#333333",
                "up": "#26a69a",
                "down": "#ef5350"
            }
        }
    except Exception as e:
        logger.error(f"Error in get_chart_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@settings_router.put("/chart-preferences")
async def update_chart_preferences(preferences: Dict[str, Any] = Body(...)):
    """Update user's chart preferences"""
    try:
        # Validate chart style
        valid_styles = ["candles", "bars", "line", "area", "heikin-ashi"]
        if "chartStyle" in preferences and preferences["chartStyle"] not in valid_styles:
            raise HTTPException(status_code=400, detail=f"Invalid chart style. Must be one of {valid_styles}")
        
        return {
            "success": True,
            "message": "Chart preferences updated successfully",
            "updatedAt": datetime.now().isoformat(),
            "preferences": preferences
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in update_chart_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@settings_router.get("/notification-preferences")
async def get_notification_preferences():
    """Get user's notification preferences"""
    try:
        return {
            "email": {
                "enabled": True,
                "tradingAlerts": True,
                "securityAlerts": True,
                "marketUpdates": False,
                "newsletterSubscribed": True
            },
            "push": {
                "enabled": True,
                "tradeExecuted": True,
                "priceAlerts": True,
                "strategiesUpdates": True
            },
            "telegram": {
                "enabled": False,
                "chatId": None
            },
            "alertFrequency": "immediate",
            "quietHours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00",
                "timezone": "UTC"
            }
        }
    except Exception as e:
        logger.error(f"Error in get_notification_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@settings_router.put("/notification-preferences")
async def update_notification_preferences(preferences: Dict[str, Any] = Body(...)):
    """Update user's notification preferences"""
    try:
        return {
            "success": True,
            "message": "Notification preferences updated successfully",
            "updatedAt": datetime.now().isoformat(),
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error in update_notification_preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
