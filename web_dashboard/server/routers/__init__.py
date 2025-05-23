"""
Router modules for the REST API server.

This package contains router modules for different API endpoints,
organized by functional area.
"""

from fastapi import APIRouter

# Import routers
from .trading import trading_router
from .exchanges import exchange_router
from .distributor import distributor_router
from .settings import settings_router
from .risk import risk_router
from .analysis import analysis_router

# Create main router
api_router = APIRouter()

# Include all routers
api_router.include_router(trading_router)
api_router.include_router(exchange_router)
api_router.include_router(risk_router)
api_router.include_router(distributor_router)
api_router.include_router(settings_router)
api_router.include_router(analysis_router)
