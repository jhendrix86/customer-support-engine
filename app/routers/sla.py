"""
SLA router - every endpoint now computes from real Ticket/Response data,
and /escalate delivers a real notification via notification-engine.
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.database import get_db
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.services.notification_client import send_escalation_alert
from app.services.support_metrics import average, first_response_hours_by_ticket, is_within_sla

router = APIRouter()

_OPEN_STATUSES = [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER, TicketStatus.ESCALATED]
_APPROACHING_WINDOW_HOURS = 2


@router.get("/status")
async def get_sla_status(db: AsyncSession = Depends(get_db)):
    """Real SLA compliance computed from every ticket in the database"""
    try:
        result = await db.execute(select(Ticket))
        tickets = result.scalars().all()
        now = datetime.utcnow()

        within = [t for t in tickets if is_within_sla(t, now)]
        approaching = [
            t for t in tickets
            if t in within and t.status in _OPEN_STATUSES and t.sla_deadline
            and t.sla_deadline - now <= timedelta(hours=_APPROACHING_WINDOW_HOURS)
        ]
        past = [t for t in tickets if t not in within]

        response_hours = await first_response_hours_by_ticket(db, [t.id for t in tickets])

        def priority_breakdown(priority: TicketPriority) -> dict:
            in_priority = [t for t in tickets if t.priority == priority]
            within_priority = [t for t in in_priority if t in within]
            compliance = round(100 * len(within_priority) / len(in_priority), 1) if in_priority else None
            avg_response = average([response_hours[t.id] for t in in_priority if t.id in response_hours])
            return {"compliance": compliance, "avg_response": avg_response}

        status = {
            "total_tickets": len(tickets),
            "tickets_within_sla": len(within),
            "tickets_approaching_sla": len(approaching),
            "tickets_past_sla": len(past),
            "sla_compliance_rate": round(100 * len(within) / len(tickets), 1) if tickets else None,
            "average_response_time": average(list(response_hours.values())),
            "by_priority": {p.value: priority_breakdown(p) for p in TicketPriority},
        }

        return status

    except Exception as e:
        logger.error(f"Failed to get SLA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def get_sla_violations(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Real SLA violations - tickets that are flagged violated, or open and past their real deadline"""
    try:
        now = datetime.utcnow()
        result = await db.execute(select(Ticket))
        tickets = result.scalars().all()

        violating = [t for t in tickets if not is_within_sla(t, now)]
        violating.sort(key=lambda t: t.sla_deadline or now)

        page = violating[offset : offset + limit]

        violations = []
        for t in page:
            reference_time = t.resolved_at or now
            hours_overdue = round((reference_time - t.sla_deadline).total_seconds() / 3600, 1) if t.sla_deadline else None
            violations.append({
                "ticket_id": str(t.id),
                "priority": t.priority.value,
                "status": t.status.value,
                "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
                "hours_overdue": hours_overdue,
            })

        return {"total": len(violating), "violations": violations, "pagination": {"limit": limit, "offset": offset}}

    except Exception as e:
        logger.error(f"Failed to get SLA violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalate/{ticket_id}")
async def escalate_sla_violation(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Escalate an SLA violation - a real status change plus a real delivered notification"""
    try:
        try:
            ticket_uuid = uuid.UUID(ticket_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

        ticket = await db.get(Ticket, ticket_uuid)
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

        logger.info(f"Escalating SLA violation for ticket {ticket_id}")

        ticket.status = TicketStatus.ESCALATED
        await db.commit()
        await db.refresh(ticket)

        notify_result = await send_escalation_alert(
            settings.support_email,
            f"SLA violation escalated: ticket {ticket_id}",
            f"Ticket \"{ticket.subject}\" ({ticket.priority.value}) has breached its SLA deadline and been escalated.",
        )

        logger.info(f"SLA violation escalated for ticket {ticket_id}, notification {'sent' if notify_result.success else 'failed'}")
        return {
            "ticket_id": ticket_id,
            "escalated": True,
            "status": ticket.status.value,
            "notified": notify_result.success,
            "notification_error": notify_result.error,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to escalate SLA violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
