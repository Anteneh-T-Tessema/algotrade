"""
Distributor router module for the FastAPI server

This module contains routes for the multi-tier distribution system:
- Commission tracking
- Referral management
- Network visualization
- Tier structure
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
distributor_router = APIRouter(
    prefix="/distributor",
    tags=["distributor"]
)

@distributor_router.get("/stats")
async def get_distributor_stats(
    period: str = "1month",
    userId: Optional[str] = None
):
    """Get distributor performance statistics"""
    try:
        # Define period in days
        days = 30
        if period == "1week":
            days = 7
        elif period == "3months":
            days = 90
        elif period == "6months":
            days = 180
        elif period == "1year":
            days = 365
        
        # Generate historical stats
        historical_data = []
        
        new_referrals_base = 3
        earnings_base = 500
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            
            # Some randomness but with trend
            new_referrals = max(0, int(np.random.normal(new_referrals_base, 2)))
            earnings = max(0, round(np.random.normal(earnings_base, earnings_base * 0.2), 2))
            
            # Slight upward trend
            new_referrals_base += 0.05
            earnings_base *= 1.01
            
            historical_data.append({
                "date": date,
                "new_referrals": new_referrals,
                "earnings": earnings,
                "active_users": int(new_referrals * np.random.uniform(5, 10))
            })
        
        return {
            "period": period,
            "total_earnings": round(sum(day["earnings"] for day in historical_data), 2),
            "total_referrals": sum(day["new_referrals"] for day in historical_data),
            "historical_data": historical_data,
            "tier_breakdown": {
                "tier1": round(np.random.uniform(1000, 5000), 2),
                "tier2": round(np.random.uniform(500, 3000), 2),
                "tier3": round(np.random.uniform(100, 1000), 2),
            }
        }
    except Exception as e:
        logger.error(f"Error in get_distributor_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@distributor_router.get("/referrals")
async def get_distributor_referrals(
    status: str = "all",
    page: int = 1,
    limit: int = 20
):
    """Get referral information"""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Mock total count
        total_count = 87
        
        # Generate mock referrals
        referrals = []
        
        for i in range(offset, min(offset + limit, total_count)):
            referral_status = np.random.choice(["active", "pending", "inactive"], p=[0.7, 0.2, 0.1])
            
            # Skip if filtering by status
            if status != "all" and status != referral_status:
                continue
            
            days_ago = np.random.randint(1, 180)
            signup_date = datetime.now() - timedelta(days=days_ago)
            
            referral = {
                "id": f"ref-{i}",
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "signup_date": signup_date.strftime("%Y-%m-%d"),
                "status": referral_status,
                "tier": np.random.randint(1, 4),
                "earnings_generated": round(np.random.uniform(50, 2000), 2),
                "active_days": max(0, int(180 - days_ago) * np.random.uniform(0.5, 0.9))
            }
            
            referrals.append(referral)
        
        return {
            "referrals": referrals,
            "total": total_count,
            "page": page,
            "limit": limit,
            "pages": (total_count + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"Error in get_distributor_referrals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@distributor_router.post("/referral-link")
async def generate_referral_link():
    """Generate a new referral link"""
    try:
        # Generate random referral code
        import string
        import random
        
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(8))
        
        # Mock domain
        domain = "https://cryptotrading-platform.com"
        
        return {
            "referralLink": f"{domain}/signup?ref={code}",
            "code": code,
            "created": datetime.now().isoformat(),
            "expires": None  # No expiration
        }
    except Exception as e:
        logger.error(f"Error in generate_referral_link: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@distributor_router.get("/commission-calculator")
async def get_commission_calculator(amount: float, tier: Optional[int] = None):
    """Calculate potential commissions based on amount and tier"""
    try:
        # Define commission rates by tier
        tier_rates = {
            1: 0.05,  # 5% for tier 1
            2: 0.08,  # 8% for tier 2
            3: 0.10,  # 10% for tier 3
        }
        
        results = {}
        
        # If tier specified, calculate just for that tier
        if tier is not None:
            if tier not in tier_rates:
                raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
            
            rate = tier_rates[tier]
            commission = amount * rate
            results[f"tier{tier}"] = round(commission, 2)
        else:
            # Calculate for all tiers
            for tier_num, rate in tier_rates.items():
                commission = amount * rate
                results[f"tier{tier_num}"] = round(commission, 2)
        
        return {
            "amount": amount,
            "commissions": results,
            "total": round(sum(results.values()), 2) if not tier else results[f"tier{tier}"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in get_commission_calculator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
