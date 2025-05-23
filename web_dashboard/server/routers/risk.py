"""
Risk Management router module for the FastAPI server

This module contains routes for risk management-related endpoints including:
- Portfolio risk analysis
- Value at Risk (VaR) calculations
- Stress testing
- Hedging recommendations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
import logging
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import risk management utilities
from utils.risk_management import RiskManager

# Set up logger
logger = logging.getLogger('api_server')

# Create router
risk_router = APIRouter(
    prefix="/risk",
    tags=["risk"]
)

@risk_router.post("/analysis")
async def get_detailed_risk_analysis(positions: List[Dict[str, Any]]):
    """
    Calculate detailed risk analysis for a portfolio of positions
    
    Args:
        positions: List of position objects with symbol, allocation, and value
    
    Returns:
        Dict containing risk metrics like diversification score, 
        asset correlations, exposure by asset class, etc.
    """
    try:
        # This would normally use actual historical data and proper risk models
        # For now, generate simulated risk analysis
        
        # Basic validation
        if not positions:
            raise HTTPException(status_code=400, detail="No positions provided")
            
        total_value = sum(position.get('value', 0) for position in positions)
        if total_value <= 0:
            raise HTTPException(status_code=400, detail="Invalid portfolio value")
        
        # Calculate asset allocations
        allocations = {}
        for position in positions:
            symbol = position.get('symbol', '')
            if not symbol:
                continue
                
            value = position.get('value', 0)
            alloc_pct = (value / total_value) * 100 if total_value > 0 else 0
            allocations[symbol] = alloc_pct
            
        # Generate simulated metrics
        # In a real implementation, these would be calculated from actual data
        diversification_score = min(len(positions) * 10, 100) / 100  # Simple score based on number of assets
        total_risk_score = 0.7 - (diversification_score * 0.2)  # Lower is better
        
        # Create correlation matrix (simulated)
        symbols = [p.get('symbol') for p in positions]
        correlation_matrix = {}
        for i, sym1 in enumerate(symbols):
            correlation_matrix[sym1] = {}
            for j, sym2 in enumerate(symbols):
                if sym1 == sym2:
                    correlation_matrix[sym1][sym2] = 1.0
                else:
                    # Generate random correlation between 0.3 and 0.9
                    correlation_matrix[sym1][sym2] = round(0.3 + (0.6 * ((i * j) % 10) / 10), 2)
        
        return {
            "totalValue": total_value,
            "diversificationScore": round(diversification_score, 2),
            "riskScore": round(total_risk_score, 2),
            "allocations": allocations,
            "correlationMatrix": correlation_matrix,
            "riskByAsset": {
                symbol: {
                    "volatility": round(0.2 + (0.4 * (i % 5) / 5), 2),  # 20-60% simulated volatility
                    "contribution": round((allocations[symbol] / 100) * total_risk_score, 3),
                } for i, symbol in enumerate(symbols)
            },
            "riskForecast": {
                "shortTerm": "moderate" if total_risk_score < 0.6 else "high",
                "mediumTerm": "low" if total_risk_score < 0.5 else "moderate"
            }
        }
    except KeyError as e:
        logger.error(f"Missing key in risk analysis data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing data for risk analysis: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid value in risk analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid value for risk analysis: {str(e)}")
    except TypeError as e:
        logger.error(f"Type error in risk analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Type error in risk analysis: {str(e)}")
    except ZeroDivisionError as e:
        logger.error(f"Division by zero in risk analysis: {str(e)}")
        raise HTTPException(status_code=400, detail="Division by zero in risk calculation")
    except ArithmeticError as e:
        logger.error(f"Arithmetic error in risk calculation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Calculation error in risk analysis: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error calculating risk analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@risk_router.post("/var")
async def get_value_at_risk(positions: List[Dict[str, Any]], confidence_level: int = 95):
    """
    Calculate Value at Risk (VaR) for a portfolio of positions
    
    Args:
        positions: List of position objects with symbol, allocation, and value
        confidence_level: Confidence level for VaR (e.g., 95 for 95%)
        
    Returns:
        Dict containing VaR metrics
    """
    try:
        # This would normally use actual historical data and proper risk models
        # For now, generate simulated VaR analysis
        
        if not positions:
            raise HTTPException(status_code=400, detail="No positions provided")
            
        total_value = sum(position.get('value', 0) for position in positions)
        if total_value <= 0:
            raise HTTPException(status_code=400, detail="Invalid portfolio value")
        
        # Generate simulated VaR values
        # In reality, these would be calculated using historical volatility and proper statistical methods
        daily_var_pct = 0.025  # 2.5% simulated daily VaR at 95% confidence
        weekly_var_pct = daily_var_pct * 2.5  # Simple approximation
        monthly_var_pct = daily_var_pct * 5  # Simple approximation
        
        daily_var_amount = total_value * daily_var_pct
        weekly_var_amount = total_value * weekly_var_pct
        monthly_var_amount = total_value * monthly_var_pct
        
        # Adjust based on confidence level
        factor = (confidence_level - 90) / 10 if confidence_level >= 90 else 0.5
        multiplier = 1 + (factor * 0.5)  # Higher confidence = higher VaR
        
        return {
            "confidenceLevel": confidence_level,
            "daily": {
                "percent": round(daily_var_pct * multiplier * 100, 2),
                "amount": round(daily_var_amount * multiplier, 2)
            },
            "weekly": {
                "percent": round(weekly_var_pct * multiplier * 100, 2),
                "amount": round(weekly_var_amount * multiplier, 2)
            },
            "monthly": {
                "percent": round(monthly_var_pct * multiplier * 100, 2),
                "amount": round(monthly_var_amount * multiplier, 2)
            },
            "methodology": "Historical Simulation (simulated)",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating VaR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate VaR: {str(e)}")


@risk_router.post("/stresstest")
async def get_portfolio_stress_test(positions: List[Dict[str, Any]], scenario: str = "bearMarket"):
    """
    Perform stress testing on a portfolio based on historical or hypothetical scenarios
    
    Args:
        positions: List of position objects with symbol, allocation, and value
        scenario: The stress scenario to test ("bearMarket", "marketCrash", "inflation", etc.)
    
    Returns:
        Dict containing projected losses and impacts under the stress scenario
    """
    try:
        if not positions:
            raise HTTPException(status_code=400, detail="No positions provided")
            
        total_value = sum(position.get('value', 0) for position in positions)
        if total_value <= 0:
            raise HTTPException(status_code=400, detail="Invalid portfolio value")
        
        # Define scenario impacts (in a real system these would be backed by actual scenario modeling)
        scenarios = {
            "bearMarket": {
                "description": "Prolonged market downturn with 20-30% decline",
                "impactMultipliers": {
                    "BTC": -0.40,  # Bitcoin would lose 40% in this scenario
                    "ETH": -0.45,  # Ethereum would lose 45%
                    "SOL": -0.55,  # Solana would lose 55%
                    "BNB": -0.35,  # Binance Coin would lose 35%
                    "default": -0.30  # Default for other assets
                },
                "duration": "3-6 months",
                "probability": "moderate"
            },
            "marketCrash": {
                "description": "Sudden market crash with 40-60% decline",
                "impactMultipliers": {
                    "BTC": -0.60,
                    "ETH": -0.65,
                    "SOL": -0.75,
                    "BNB": -0.60,
                    "default": -0.50
                },
                "duration": "1-3 months",
                "probability": "low"
            },
            "inflation": {
                "description": "High inflation scenario with rising interest rates",
                "impactMultipliers": {
                    "BTC": -0.20,
                    "ETH": -0.25,
                    "SOL": -0.30,
                    "BNB": -0.20,
                    "default": -0.15
                },
                "duration": "6-12 months",
                "probability": "moderate"
            },
            "regulatoryAction": {
                "description": "Major regulatory action against cryptocurrencies",
                "impactMultipliers": {
                    "BTC": -0.35,
                    "ETH": -0.40,
                    "SOL": -0.50,
                    "BNB": -0.45,
                    "default": -0.30
                },
                "duration": "3-9 months",
                "probability": "moderate"
            }
        }
        
        # If scenario doesn't exist, use bearMarket as default
        if scenario not in scenarios:
            scenario = "bearMarket"
            
        scenario_data = scenarios[scenario]
        multipliers = scenario_data["impactMultipliers"]
        
        # Calculate impact on each position and total
        impacts = []
        total_loss = 0
        
        for position in positions:
            symbol = position.get('symbol', '')
            if not symbol:
                continue
                
            value = position.get('value', 0)
            
            # Get the first part of the symbol (e.g. 'BTC' from 'BTCUSDT')
            base_symbol = symbol.split('/')[0] if '/' in symbol else symbol.split('USDT')[0] if 'USDT' in symbol else symbol
            
            # Get the multiplier for this asset
            multiplier = multipliers.get(base_symbol, multipliers.get("default", -0.30))
            
            impact_amount = value * multiplier
            total_loss += impact_amount
            
            impacts.append({
                "symbol": symbol,
                "currentValue": value,
                "impactPercent": multiplier * 100,
                "impactAmount": impact_amount,
                "projectedValue": value + impact_amount
            })
        
        return {
            "scenario": scenario,
            "description": scenario_data["description"],
            "duration": scenario_data["duration"],
            "probability": scenario_data["probability"],
            "totalCurrentValue": total_value,
            "totalImpactAmount": total_loss,
            "totalImpactPercent": (total_loss / total_value) * 100 if total_value > 0 else 0,
            "projectedPortfolioValue": total_value + total_loss,
            "impacts": impacts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error performing stress test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform stress test: {str(e)}")


@risk_router.post("/hedging")
async def get_hedging_recommendations(positions: List[Dict[str, Any]]):
    """
    Provide recommendations for hedging a portfolio to reduce risk
    
    Args:
        positions: List of position objects with symbol, allocation, and value
    
    Returns:
        List of hedging strategies and specific recommendations
    """
    try:
        if not positions:
            raise HTTPException(status_code=400, detail="No positions provided")
            
        total_value = sum(position.get('value', 0) for position in positions)
        if total_value <= 0:
            raise HTTPException(status_code=400, detail="Invalid portfolio value")
        
        # In a real implementation, these would be based on actual portfolio analysis
        # and hedging strategies appropriate for the current market conditions
        
        # Get the symbols in the portfolio
        symbols = [p.get('symbol', '').split('USDT')[0] if 'USDT' in p.get('symbol', '') else p.get('symbol', '').split('/')[0] for p in positions]
        
        # Generate some basic hedging recommendations
        recommendations = [
            {
                "type": "options",
                "description": "Purchase put options to protect against downside",
                "targetAssets": symbols[:2],  # Just the first two assets as an example
                "estimatedCost": round(total_value * 0.01, 2),  # 1% of portfolio value
                "potentialBenefit": "Protection against 15-20% downside movement",
                "complexity": "moderate"
            },
            {
                "type": "futures",
                "description": "Short futures contracts to hedge long positions",
                "targetAssets": symbols,
                "estimatedCost": round(total_value * 0.005, 2),  # 0.5% of portfolio value
                "potentialBenefit": "Direct hedge against price declines",
                "complexity": "high"
            },
            {
                "type": "diversification",
                "description": "Diversify into uncorrelated assets to reduce overall portfolio risk",
                "recommendedAssets": ["GOLD", "USD", "LINK"],
                "allocationPercentage": 20,  # Recommend allocating 20% to these assets
                "estimatedCost": "Minimal (trading fees only)",
                "potentialBenefit": "Reduced overall portfolio volatility",
                "complexity": "low"
            },
            {
                "type": "stablecoin",
                "description": "Convert a portion of holdings to stablecoins to reduce exposure",
                "recommendedPercentage": 25,  # Recommend converting 25% to stablecoins
                "estimatedCost": "Minimal (trading fees only)",
                "potentialBenefit": "Immediate risk reduction while maintaining crypto exposure",
                "complexity": "low"
            }
        ]
        
        return {
            "portfolioValue": total_value,
            "currentRiskLevel": "high" if len(positions) < 3 else "medium" if len(positions) < 5 else "moderate",
            "recommendations": recommendations,
            "disclaimer": "These are algorithmic recommendations. Always consult with a financial advisor before implementing hedging strategies.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating hedging recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate hedging recommendations: {str(e)}")
