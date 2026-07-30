"""
Ticket router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketChannel

router = APIRouter()


class CreateTicketRequest(BaseModel):
    """Request to create ticket"""
    customer_id: str
    customer_name: str
    customer_email: str
    subject: str
    message: str
    priority: str = "medium"
    channel: str = "email"


class ResolveTicketRequest(BaseModel):
    """Request to resolve ticket"""
    resolution_notes: str


class AssignTicketRequest(BaseModel):
    """Request to assign ticket"""
    agent_id: str


@router.post("/create")
async def create_ticket(
    request: CreateTicketRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a support ticket"""
    try:
        logger.info(f"Creating ticket from {request.customer_email}: {request.subject}")
        
        # Calculate SLA deadline based on priority
        if request.priority == "critical":
            sla_deadline = datetime.utcnow() + timedelta(hours=1)
        elif request.priority == "high":
            sla_deadline = datetime.utcnow() + timedelta(hours=4)
        elif request.priority == "medium":
            sla_deadline = datetime.utcnow() + timedelta(hours=24)
        else:
            sla_deadline = datetime.utcnow() + timedelta(hours=48)
        
        # In production, this would save to database
        # For now, return a mock response
        ticket = {
            "id": "ticket_123",
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "subject": request.subject,
            "message": request.message,
            "priority": request.priority,
            "status": "open",
            "channel": request.channel,
            "sla_deadline": sla_deadline.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Ticket created: {ticket['id']}")
        return ticket
        
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    request: ResolveTicketRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a ticket"""
    try:
        logger.info(f"Resolving ticket {ticket_id}")
        
        # In production, this would update database
        # For now, return a mock response
        ticket = {
            "id": ticket_id,
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": request.resolution_notes
        }
        
        logger.info(f"Ticket resolved: {ticket_id}")
        return ticket
        
    except Exception as e:
        logger.error(f"Failed to resolve ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Escalate a ticket"""
    try:
        logger.info(f"Escalating ticket {ticket_id}")
        
        # In production, this would update database and notify
        # For now, return a mock response
        ticket = {
            "id": ticket_id,
            "status": "escalated",
            "escalated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Ticket escalated: {ticket_id}")
        return ticket
        
    except Exception as e:
        logger.error(f"Failed to escalate ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    request: AssignTicketRequest,
    db: AsyncSession = Depends(get_db)
):
    """Assign ticket to agent"""
    try:
        logger.info(f"Assigning ticket {ticket_id} to agent {request.agent_id}")
        
        # In production, this would update database
        # For now, return a mock response
        ticket = {
            "id": ticket_id,
            "assigned_agent_id": request.agent_id,
            "status": "in_progress",
            "assigned_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Ticket assigned: {ticket_id}")
        return ticket
        
    except Exception as e:
        logger.error(f"Failed to assign ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get ticket details"""
    try:
        logger.info(f"Getting ticket details for {ticket_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        ticket = {
            "id": ticket_id,
            "customer_id": "cust_123",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "subject": "Payment processing issue",
            "message": "My payment failed to process",
            "priority": "high",
            "status": "in_progress",
            "channel": "email",
            "assigned_agent_id": "agent_123",
            "sla_deadline": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return ticket
        
    except Exception as e:
        logger.error(f"Failed to get ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List tickets"""
    try:
        logger.info("Listing tickets")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        tickets = [
            {
                "id": "ticket_001",
                "customer_email": "john@example.com",
                "subject": "Payment processing issue",
                "priority": "high",
                "status": "in_progress",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "ticket_002",
                "customer_email": "jane@example.com",
                "subject": "Feature request",
                "priority": "low",
                "status": "open",
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return {
            "total": len(tickets),
            "tickets": tickets,
            "filters": {
                "status": status,
                "priority": priority,
                "customer_id": customer_id
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
