"""
Analytics router - every endpoint now computes from real Ticket/Agent/
Customer/Response data instead of returning fixed literals.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models.agent import Agent
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketStatus
from app.services.support_metrics import average, first_response_hours_by_ticket

router = APIRouter()

_RESOLVED_STATUSES = [TicketStatus.RESOLVED, TicketStatus.CLOSED]


@router.get("/metrics")
async def get_support_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Real support metrics computed over tickets created in the given window"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await db.execute(select(Ticket).where(Ticket.created_at >= start_date, Ticket.created_at <= end_date))
        tickets = result.scalars().all()

        resolved = [t for t in tickets if t.status in _RESOLVED_STATUSES]
        escalated = [t for t in tickets if t.status == TicketStatus.ESCALATED]
        open_tickets = [t for t in tickets if t.status not in _RESOLVED_STATUSES]

        resolution_hours = [
            (t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved if t.resolved_at
        ]
        response_hours = await first_response_hours_by_ticket(db, [t.id for t in tickets])

        response_counts = await _response_counts_by_ticket(db, [t.id for t in resolved])
        first_contact_resolved = sum(1 for t in resolved if response_counts.get(t.id, 0) <= 1)

        def channel_or_priority_breakdown(tickets_list, get_key):
            buckets = defaultdict(list)
            for t in tickets_list:
                key = get_key(t)
                buckets[key].append(t)
            return {
                key: {
                    "count": len(bucket),
                    "avg_response": average([response_hours[t.id] for t in bucket if t.id in response_hours]),
                }
                for key, bucket in buckets.items()
            }

        metrics = {
            "total_tickets": len(tickets),
            "open_tickets": len(open_tickets),
            "resolved_tickets": len(resolved),
            "escalated_tickets": len(escalated),
            "average_response_time": average(list(response_hours.values())),
            "average_resolution_time": average(resolution_hours),
            "first_contact_resolution_rate": round(100 * first_contact_resolved / len(resolved), 1) if resolved else None,
            "by_channel": channel_or_priority_breakdown(tickets, lambda t: t.channel.value),
            "by_priority": channel_or_priority_breakdown(tickets, lambda t: t.priority.value),
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        }

        return metrics

    except Exception as e:
        logger.error(f"Failed to get support metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _response_counts_by_ticket(db: AsyncSession, ticket_ids: list) -> dict:
    from sqlalchemy import func
    from app.models.response import Response

    if not ticket_ids:
        return {}
    result = await db.execute(
        select(Response.ticket_id, func.count(Response.id)).where(Response.ticket_id.in_(ticket_ids)).group_by(Response.ticket_id)
    )
    return dict(result.all())


@router.get("/performance")
async def get_agent_performance(db: AsyncSession = Depends(get_db)):
    """Real per-agent performance, aggregated from tickets actually assigned to each agent"""
    try:
        agents_result = await db.execute(select(Agent))
        agents = agents_result.scalars().all()

        tickets_result = await db.execute(select(Ticket).where(Ticket.assigned_agent_id.isnot(None)))
        tickets = tickets_result.scalars().all()

        response_hours = await first_response_hours_by_ticket(db, [t.id for t in tickets])
        response_counts = await _response_counts_by_ticket(db, [t.id for t in tickets])

        performance = []
        for agent in agents:
            agent_tickets = [t for t in tickets if t.assigned_agent_id == agent.id]
            resolved = [t for t in agent_tickets if t.status in _RESOLVED_STATUSES and t.resolved_at]
            resolution_hours = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved]
            csat_scores = [t.csat_score for t in agent_tickets if t.csat_score is not None]
            first_contact = sum(1 for t in resolved if response_counts.get(t.id, 0) <= 1)

            performance.append({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "tickets_handled": len(agent_tickets),
                "average_response_time": average([response_hours[t.id] for t in agent_tickets if t.id in response_hours]),
                "average_resolution_time": average(resolution_hours),
                "average_csat": average(csat_scores),
                "first_contact_resolution_rate": round(100 * first_contact / len(resolved), 1) if resolved else None,
            })

        performance.sort(key=lambda p: p["tickets_handled"], reverse=True)
        return {"total": len(performance), "agents": performance}

    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satisfaction")
async def get_csat_scores(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Real CSAT aggregation from actual ticket csat_score values"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await db.execute(
            select(Ticket).where(Ticket.created_at >= start_date, Ticket.created_at <= end_date)
        )
        tickets = result.scalars().all()
        resolved = [t for t in tickets if t.status in _RESOLVED_STATUSES]
        scored = [t for t in tickets if t.csat_score is not None]

        by_score = defaultdict(int)
        for t in scored:
            by_score[str(t.csat_score)] += 1

        customer_ids = {t.customer_id for t in scored}
        tiers_by_customer = {}
        if customer_ids:
            customers_result = await db.execute(select(Customer).where(Customer.id.in_(customer_ids)))
            tiers_by_customer = {c.id: c.tier.value for c in customers_result.scalars().all()}

        by_tier_scores = defaultdict(list)
        for t in scored:
            tier = tiers_by_customer.get(t.customer_id, "unknown")
            by_tier_scores[tier].append(t.csat_score)

        by_day_scores = defaultdict(list)
        for t in scored:
            day = t.created_at.date().isoformat()
            by_day_scores[day].append(t.csat_score)

        csat = {
            "average_csat": average([t.csat_score for t in scored]),
            "total_surveys": len(scored),
            "response_rate": round(100 * len(scored) / len(resolved), 1) if resolved else None,
            "by_score": dict(by_score),
            "by_tier": {tier: {"avg_csat": average(scores), "surveys": len(scores)} for tier, scores in by_tier_scores.items()},
            "trend": [{"date": day, "csat": average(scores)} for day, scores in sorted(by_day_scores.items())],
        }

        return csat

    except Exception as e:
        logger.error(f"Failed to get CSAT scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))
