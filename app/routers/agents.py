"""
Agent router - real DB-backed CRUD against the agents table.

Didn't exist at all before this pass - the Agent model was already
real and Ticket.assigned_agent_id already pointed at it, but there was
no way to ever create an Agent row via the API, so /tickets/{id}/assign
could never succeed against anything real. Same class of gap as
integration-engine's missing webhook-registration endpoint last session.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.agent import Agent, AgentStatus
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateAgentRequest(BaseModel):
    """Request to create a support agent"""
    name: str
    email: str
    specialization: Optional[list] = None


def _serialize(agent: Agent) -> dict:
    return {
        "id": str(agent.id),
        "name": agent.name,
        "email": agent.email,
        "status": agent.status.value,
        "total_tickets_handled": agent.total_tickets_handled,
        "average_response_time": agent.average_response_time,
        "average_csat": agent.average_csat,
        "specialization": agent.specialization,
        "created_at": agent.created_at.isoformat(),
    }


async def _get_agent_or_404(db: AsyncSession, agent_id: str) -> Agent:
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    agent = await db.get(Agent, agent_uuid)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.post("/create")
async def create_agent(request: CreateAgentRequest, db: AsyncSession = Depends(get_db)):
    """Create a support agent"""
    try:
        logger.info(f"Creating agent: {request.name}")

        agent = Agent(name=request.name, email=request.email, specialization=request.specialization)
        apply_tenant_context(agent)

        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        logger.info(f"Agent created: {agent.id}")
        return _serialize(agent)

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get agent details"""
    try:
        agent = await _get_agent_or_404(db, agent_id)
        return _serialize(agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_agents(status: Optional[AgentStatus] = None, db: AsyncSession = Depends(get_db)):
    """List agents, real filters applied against the database"""
    try:
        query = select(Agent)
        if status is not None:
            query = query.where(Agent.status == status)

        result = await db.execute(query.order_by(Agent.name))
        agents = result.scalars().all()

        return {"total": len(agents), "agents": [_serialize(a) for a in agents]}

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
