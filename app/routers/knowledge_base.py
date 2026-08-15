"""
Knowledge base router - real DB-backed CRUD, and /search does a real
text query (app/services/kb_search.py) instead of returning 2 fixed
payment-related articles regardless of the query.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.knowledge_article import KnowledgeArticle
from app.models.tenant_base import apply_tenant_context
from app.models.ticket import Ticket
from app.services.kb_search import search_articles

router = APIRouter()


class CreateArticleRequest(BaseModel):
    """Request to create a knowledge base article"""
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list] = None


class SearchRequest(BaseModel):
    """Request to search knowledge base"""
    query: str
    limit: int = 5


def _serialize(article: KnowledgeArticle, relevance: Optional[float] = None) -> dict:
    body = {
        "id": str(article.id),
        "title": article.title,
        "content": article.content,
        "category": article.category,
        "tags": article.tags,
        "view_count": article.view_count,
        "helpful_count": article.helpful_count,
        "not_helpful_count": article.not_helpful_count,
        "is_published": article.is_published,
    }
    if relevance is not None:
        body["relevance"] = relevance
    return body


async def _get_article_or_404(db: AsyncSession, article_id: str) -> KnowledgeArticle:
    try:
        article_uuid = uuid.UUID(article_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Article '{article_id}' not found")

    article = await db.get(KnowledgeArticle, article_uuid)
    if article is None:
        raise HTTPException(status_code=404, detail=f"Article '{article_id}' not found")
    return article


@router.post("/articles")
async def create_article(request: CreateArticleRequest, db: AsyncSession = Depends(get_db)):
    """Create a knowledge base article"""
    try:
        logger.info(f"Creating KB article: {request.title}")

        article = KnowledgeArticle(title=request.title, content=request.content, category=request.category, tags=request.tags)
        apply_tenant_context(article)

        db.add(article)
        await db.commit()
        await db.refresh(article)

        logger.info(f"KB article created: {article.id}")
        return _serialize(article)

    except Exception as e:
        logger.error(f"Failed to create article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge_base(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Search knowledge base - a real ilike/term-overlap search, not fixed results"""
    try:
        logger.info(f"Searching knowledge base for: {request.query}")

        matches = await search_articles(db, request.query, request.limit)

        return {
            "query": request.query,
            "total": len(matches),
            "articles": [_serialize(m["article"], m["relevance"]) for m in matches],
        }

    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest/{ticket_id}")
async def suggest_articles(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Suggest articles for a real ticket, based on its own subject + message"""
    try:
        try:
            ticket_uuid = uuid.UUID(ticket_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

        ticket = await db.get(Ticket, ticket_uuid)
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

        matches = await search_articles(db, f"{ticket.subject} {ticket.message}", limit=3)

        return {
            "ticket_id": ticket_id,
            "suggestions": [
                {"article_id": str(m["article"].id), "title": m["article"].title, "relevance": m["relevance"]}
                for m in matches
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suggest articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    """Get article details - a real view, incrementing the real view_count"""
    try:
        article = await _get_article_or_404(db, article_id)

        article.view_count = (article.view_count or 0) + 1
        await db.commit()
        await db.refresh(article)

        return _serialize(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(status_code=500, detail=str(e))
