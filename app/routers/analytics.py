"""
Analytics router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


@router.get("/metrics")
async def get_support_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get support metrics"""
    try:
        logger.info("Getting support metrics")
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        # In production, this would calculate from database
        # For now, return a mock response
        metrics = {
            "total_tickets": 150,
            "open_tickets": 25,
            "resolved_tickets": 120,
            "escalated_tickets": 5,
            "average_response_time": 2.5,  # hours
            "average_resolution_time": 18.0,  # hours
            "first_contact_resolution_rate": 75.0,  # percentage
            "by_channel": {
                "email": {"count": 80, "avg_response": 3.0},
                "chat": {"count": 50, "avg_response": 1.5},
                "phone": {"count": 15, "avg_response": 2.0},
                "social": {"count": 5, "avg_response": 4.0}
            },
            "by_priority": {
                "critical": {"count": 10, "avg_response": 0.8},
                "high": {"count": 40, "avg_response": 2.0},
                "medium": {"count": 70, "avg_response": 3.0},
                "low": {"count": 30, "avg_response": 4.0}
            },
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get support metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_agent_performance(
    db: AsyncSession = Depends(get_db)
):
    """Get agent performance"""
    try:
        logger.info("Getting agent performance")
        
        # In production, this would calculate from database
        # For now, return a mock response
        performance = [
            {
                "agent_id": "agent_001",
                "agent_name": "Alice Johnson",
                "tickets_handled": 45,
                "average_response_time": 2.0,
                "average_resolution_time": 15.0,
                "average_csat": 4.5,
                "first_contact_resolution_rate": 80.0
            },
            {
                "agent_id": "agent_002",
                "agent_name": "Bob Smith",
                "tickets_handled": 35,
                "average_response_time": 2.5,
                "average_resolution_time": 18.0,
                "average_csat": 4.3,
                "first_contact_resolution_rate": 72.0
            }
        ]
        
        return {
            "total": len(performance),
            "agents": performance
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satisfaction")
async def get_csat_scores(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get CSAT scores"""
    try:
        logger.info("Getting CSAT scores")
        
        # In production, this would calculate from database
        # For now, return a mock response
        csat = {
            "average_csat": 4.4,  # out of 5
            "total_surveys": 100,
            "response_rate": 65.0,  # percentage
            "by_score": {
                "5": 45,
                "4": 30,
                "3": 15,
                "2": 7,
                "1": 3
            },
            "by_tier": {
                "enterprise": {"avg_csat": 4.7, "surveys": 20},
                "professional": {"avg_csat": 4.5, "surveys": 40},
                "standard": {"avg_csat": 4.3, "surveys": 30},
                "free": {"avg_csat": 4.0, "surveys": 10}
            },
            "trend": [
                {"date": "2024-01-01", "csat": 4.3},
                {"date": "2024-01-08", "csat": 4.4},
                {"date": "2024-01-15", "csat": 4.4}
            ]
        }
        
        return csat
        
    except Exception as e:
        logger.error(f"Failed to get CSAT scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
