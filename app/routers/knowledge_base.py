"""
Knowledge base router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class SearchRequest(BaseModel):
    """Request to search knowledge base"""
    query: str
    limit: int = 5


@router.post("/search")
async def search_knowledge_base(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search knowledge base"""
    try:
        logger.info(f"Searching knowledge base for: {request.query}")
        
        # In production, this would search knowledge base with embeddings
        # For now, return a mock response
        articles = [
            {
                "id": "kb_001",
                "title": "Payment Processing Troubleshooting",
                "content": "Check your payment method validity and available funds...",
                "category": "Payments",
                "relevance": 0.92
            },
            {
                "id": "kb_002",
                "title": "Common Payment Issues",
                "content": "Most payment issues are resolved by updating payment methods...",
                "category": "Payments",
                "relevance": 0.85
            }
        ]
        
        return {
            "query": request.query,
            "total": len(articles),
            "articles": articles
        }
        
    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/suggest/{ticket_id}")
async def suggest_articles(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Suggest articles for ticket"""
    try:
        logger.info(f"Suggesting articles for ticket {ticket_id}")
        
        # In production, this would analyze ticket and suggest articles
        # For now, return a mock response
        suggestions = [
            {
                "article_id": "kb_001",
                "title": "Payment Processing Troubleshooting",
                "relevance": 0.92
            }
        ]
        
        return {
            "ticket_id": ticket_id,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Failed to suggest articles: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get article details"""
    try:
        logger.info(f"Getting article {article_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        article = {
            "id": article_id,
            "title": "Payment Processing Troubleshooting",
            "content": "Check your payment method validity and available funds. If the issue persists, contact support.",
            "category": "Payments",
            "tags": ["payment", "troubleshooting", "billing"],
            "view_count": 150,
            "helpful_count": 120,
            "not_helpful_count": 5
        }
        
        return article
        
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(status_code=500, detail(str(e))
