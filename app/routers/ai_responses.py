"""
AI response router - real OpenAI-backed drafting (app/services/ai_responder.py)
and real knowledge-base suggestions, instead of a fixed canned reply.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.response import Response, ResponseType
from app.models.ticket import Ticket, TicketStatus
from app.models.tenant_base import apply_tenant_context
from app.services.ai_responder import AIResponder
from app.services.kb_search import search_articles

router = APIRouter()


class GenerateResponseRequest(BaseModel):
    """Request to generate AI response"""
    ticket_id: str
    customer_message: str
    context: Optional[str] = None


def get_ai_responder(request: Request) -> AIResponder:
    return request.app.state.ai_responder


async def _get_ticket_or_404(db: AsyncSession, ticket_id: str) -> Ticket:
    try:
        ticket_uuid = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    ticket = await db.get(Ticket, ticket_uuid)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    return ticket


@router.post("/generate-response")
async def generate_ai_response(
    request: GenerateResponseRequest,
    db: AsyncSession = Depends(get_db),
    ai_responder: AIResponder = Depends(get_ai_responder),
):
    """Generate an AI-drafted response for a real ticket - a preview, not persisted/sent"""
    try:
        await _get_ticket_or_404(db, request.ticket_id)
        logger.info(f"Generating AI response for ticket {request.ticket_id}")

        result = await ai_responder.generate_response(request.customer_message, request.context)
        matches = await search_articles(db, request.customer_message, limit=3)

        response = {
            "ticket_id": request.ticket_id,
            "success": result["success"],
            "response": result.get("body"),
            "error": result.get("error"),
            "suggested_articles": [
                {"id": str(m["article"].id), "title": m["article"].title} for m in matches
            ],
            "ai_model": result["model"],
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"AI response {'generated' if result['success'] else 'failed'} for ticket {request.ticket_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond/{ticket_id}")
async def send_ai_response(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    ai_responder: AIResponder = Depends(get_ai_responder),
):
    """Generate and persist a real AI response to a ticket, using its own message as the basis"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)
        logger.info(f"Sending AI response for ticket {ticket_id}")

        result = await ai_responder.generate_response(ticket.message)
        if not result["success"]:
            logger.warning(f"AI response for ticket {ticket_id} failed: {result.get('error')}")
            return {"ticket_id": ticket_id, "status": "failed", "error": result.get("error")}

        matches = await search_articles(db, ticket.message, limit=3)

        response = Response(
            ticket_id=ticket.id,
            message=result["body"],
            response_type=ResponseType.AI_GENERATED,
            ai_model=result["model"],
            knowledge_articles_used=[str(m["article"].id) for m in matches] or None,
        )
        apply_tenant_context(response)
        db.add(response)

        ticket.status = TicketStatus.WAITING_CUSTOMER

        await db.commit()
        await db.refresh(response)

        logger.info(f"AI response sent for ticket {ticket_id}: {response.id}")
        return {
            "ticket_id": ticket_id,
            "response_id": str(response.id),
            "status": "sent",
            "message": response.message,
            "sent_at": response.created_at.isoformat(),
            "response_type": response.response_type.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send AI response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{ticket_id}")
async def get_suggestions(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Get real knowledge base suggestions for a ticket"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)

        matches = await search_articles(db, f"{ticket.subject} {ticket.message}", limit=5)

        return {
            "ticket_id": ticket_id,
            "suggestions": [
                {
                    "article_id": str(m["article"].id),
                    "title": m["article"].title,
                    "relevance": m["relevance"],
                    "excerpt": m["article"].content[:200],
                }
                for m in matches
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
