"""
Ticket router - real DB-backed CRUD against the tickets table.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.agent import Agent
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketChannel
from app.models.tenant_base import apply_tenant_context
from app.services.sla_policy import compute_sla_deadline

router = APIRouter()


class CreateTicketRequest(BaseModel):
    """Request to create ticket"""
    customer_name: str
    customer_email: str
    subject: str
    message: str
    priority: TicketPriority = TicketPriority.MEDIUM
    channel: TicketChannel = TicketChannel.EMAIL


class ResolveTicketRequest(BaseModel):
    """Request to resolve ticket"""
    resolution_notes: str


class AssignTicketRequest(BaseModel):
    """Request to assign ticket"""
    agent_id: str


def _serialize(ticket: Ticket, customer: Optional[Customer] = None) -> dict:
    return {
        "id": str(ticket.id),
        "customer_id": str(ticket.customer_id),
        "customer_name": customer.name if customer else None,
        "customer_email": customer.email if customer else None,
        "assigned_agent_id": str(ticket.assigned_agent_id) if ticket.assigned_agent_id else None,
        "subject": ticket.subject,
        "message": ticket.message,
        "priority": ticket.priority.value,
        "status": ticket.status.value,
        "channel": ticket.channel.value,
        "sla_deadline": ticket.sla_deadline.isoformat() if ticket.sla_deadline else None,
        "sla_violated": ticket.sla_violated,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at.isoformat(),
    }


async def _get_ticket_or_404(db: AsyncSession, ticket_id: str) -> Ticket:
    try:
        ticket_uuid = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    ticket = await db.get(Ticket, ticket_uuid)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    return ticket


@router.post("/create")
async def create_ticket(request: CreateTicketRequest, db: AsyncSession = Depends(get_db)):
    """Create a support ticket - gets or creates the customer by email"""
    try:
        logger.info(f"Creating ticket from {request.customer_email}: {request.subject}")

        result = await db.execute(select(Customer).where(Customer.email == request.customer_email))
        customer = result.scalars().first()
        if customer is None:
            customer = Customer(email=request.customer_email, name=request.customer_name)
            apply_tenant_context(customer)
            db.add(customer)
            await db.flush()

        sla_deadline = compute_sla_deadline(request.priority)

        ticket = Ticket(
            customer_id=customer.id,
            subject=request.subject,
            message=request.message,
            priority=request.priority,
            status=TicketStatus.OPEN,
            channel=request.channel,
            sla_deadline=sla_deadline,
        )
        apply_tenant_context(ticket)
        db.add(ticket)

        customer.total_tickets = (customer.total_tickets or 0) + 1
        customer.open_tickets = (customer.open_tickets or 0) + 1

        await db.commit()
        await db.refresh(ticket)
        await db.refresh(customer)

        logger.info(f"Ticket created: {ticket.id}")
        return _serialize(ticket, customer)

    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: ResolveTicketRequest, db: AsyncSession = Depends(get_db)):
    """Resolve a ticket"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)

        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_notes = request.resolution_notes
        if ticket.sla_deadline and ticket.resolved_at > ticket.sla_deadline:
            ticket.sla_violated = True

        customer = await db.get(Customer, ticket.customer_id)
        if customer is not None:
            customer.open_tickets = max((customer.open_tickets or 1) - 1, 0)

        await db.commit()
        await db.refresh(ticket)

        logger.info(f"Ticket resolved: {ticket_id}")
        return _serialize(ticket)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Escalate a ticket"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)

        ticket.status = TicketStatus.ESCALATED
        await db.commit()
        await db.refresh(ticket)

        logger.info(f"Ticket escalated: {ticket_id}")
        return _serialize(ticket)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to escalate ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, request: AssignTicketRequest, db: AsyncSession = Depends(get_db)):
    """Assign ticket to a real, existing agent"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)

        try:
            agent_uuid = uuid.UUID(request.agent_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Agent '{request.agent_id}' not found")

        agent = await db.get(Agent, agent_uuid)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent '{request.agent_id}' not found")

        ticket.assigned_agent_id = agent.id
        ticket.status = TicketStatus.IN_PROGRESS
        agent.total_tickets_handled = (agent.total_tickets_handled or 0) + 1

        await db.commit()
        await db.refresh(ticket)

        logger.info(f"Ticket assigned: {ticket_id} -> agent {agent.id}")
        return _serialize(ticket)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Get ticket details"""
    try:
        ticket = await _get_ticket_or_404(db, ticket_id)
        customer = await db.get(Customer, ticket.customer_id)
        return _serialize(ticket, customer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    customer_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List tickets, real filters applied against the database"""
    try:
        query = select(Ticket)
        if status is not None:
            query = query.where(Ticket.status == status)
        if priority is not None:
            query = query.where(Ticket.priority == priority)
        if customer_id is not None:
            try:
                query = query.where(Ticket.customer_id == uuid.UUID(customer_id))
            except ValueError:
                return {"total": 0, "tickets": [], "filters": {"status": None, "priority": None, "customer_id": customer_id}, "pagination": {"limit": limit, "offset": offset}}

        query = query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        tickets = result.scalars().all()

        return {
            "total": len(tickets),
            "tickets": [_serialize(t) for t in tickets],
            "filters": {
                "status": status.value if status else None,
                "priority": priority.value if priority else None,
                "customer_id": customer_id,
            },
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
