"""
Real aggregation helpers shared by sla.py and analytics.py - both
routers report overlapping breakdowns (by priority/channel, SLA
compliance, response times) over the same Ticket/Response data, so the
actual computation lives here once.
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response
from app.models.ticket import Ticket, TicketStatus


def is_within_sla(ticket: Ticket, now: Optional[datetime] = None) -> bool:
    """
    Real per-ticket SLA check: for a resolved/closed ticket, trust the
    persisted sla_violated flag set at resolution time; for a still-open
    ticket, compare its deadline against right now.
    """
    if ticket.sla_deadline is None:
        return True
    if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        return not ticket.sla_violated
    return (now or datetime.utcnow()) <= ticket.sla_deadline


async def first_response_hours_by_ticket(db: AsyncSession, ticket_ids: List) -> Dict:
    """Real time-to-first-response per ticket, in hours, from actual Response rows."""
    if not ticket_ids:
        return {}

    result = await db.execute(
        select(Response.ticket_id, func.min(Response.created_at))
        .where(Response.ticket_id.in_(ticket_ids))
        .group_by(Response.ticket_id)
    )
    first_response_at = dict(result.all())

    tickets_result = await db.execute(select(Ticket.id, Ticket.created_at).where(Ticket.id.in_(ticket_ids)))
    created_at_by_ticket = dict(tickets_result.all())

    hours: Dict = {}
    for ticket_id, responded_at in first_response_at.items():
        created_at = created_at_by_ticket.get(ticket_id)
        if created_at is not None:
            hours[ticket_id] = (responded_at - created_at).total_seconds() / 3600
    return hours


def average(values: List[float]) -> Optional[float]:
    return round(sum(values) / len(values), 2) if values else None
