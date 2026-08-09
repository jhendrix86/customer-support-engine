"""
tickets.py is currently 100% mock (every endpoint has a "# In production,
this would ... For now, return a mock response" comment and never touches
the database) - real DB persistence for this router is a bigger, separate
task (matching content-engine/marketing-automation-engine's earlier mock ->
real conversions), not in scope here. These tests cover what's actually
true today: routing/response-shape regressions, request validation, and the
one piece of genuinely computed logic in the router - the SLA deadline math.
"""

from datetime import datetime

import pytest


async def test_create_ticket_returns_the_submitted_fields(client):
    r = await client.post("/tickets/create", json={
        "customer_id": "cust_1", "customer_name": "Jane Doe", "customer_email": "jane@example.com",
        "subject": "Can't log in", "message": "Getting an error", "priority": "high", "channel": "chat",
    })

    assert r.status_code == 200
    body = r.json()
    assert body["customer_email"] == "jane@example.com"
    assert body["subject"] == "Can't log in"
    assert body["status"] == "open"


async def test_create_ticket_requires_the_declared_fields(client):
    r = await client.post("/tickets/create", json={"customer_id": "cust_1"})
    assert r.status_code == 422


async def test_sla_deadline_matches_priority_critical(client):
    r = await client.post("/tickets/create", json={
        "customer_id": "c", "customer_name": "n", "customer_email": "e@x.com",
        "subject": "s", "message": "m", "priority": "critical",
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(3600, abs=1)  # 1 hour


async def test_sla_deadline_matches_priority_high(client):
    r = await client.post("/tickets/create", json={
        "customer_id": "c", "customer_name": "n", "customer_email": "e@x.com",
        "subject": "s", "message": "m", "priority": "high",
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(4 * 3600, abs=1)


async def test_sla_deadline_matches_priority_medium_default(client):
    r = await client.post("/tickets/create", json={
        "customer_id": "c", "customer_name": "n", "customer_email": "e@x.com", "subject": "s", "message": "m",
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(24 * 3600, abs=1)


async def test_sla_deadline_matches_priority_low(client):
    r = await client.post("/tickets/create", json={
        "customer_id": "c", "customer_name": "n", "customer_email": "e@x.com",
        "subject": "s", "message": "m", "priority": "low",
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(48 * 3600, abs=1)


async def test_resolve_ticket(client):
    r = await client.post("/tickets/ticket_123/resolve", json={"resolution_notes": "Fixed it"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


async def test_escalate_ticket(client):
    r = await client.post("/tickets/ticket_123/escalate")
    assert r.status_code == 200
    assert r.json()["status"] == "escalated"


async def test_assign_ticket(client):
    r = await client.post("/tickets/ticket_123/assign", json={"agent_id": "agent_1"})
    assert r.status_code == 200
    assert r.json()["assigned_agent_id"] == "agent_1"


async def test_get_ticket(client):
    r = await client.get("/tickets/ticket_123")
    assert r.status_code == 200
    assert r.json()["id"] == "ticket_123"


async def test_list_tickets(client):
    r = await client.get("/tickets/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["tickets"])


async def test_list_tickets_echoes_filters(client):
    r = await client.get("/tickets/", params={"status": "open", "priority": "high"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"status": "open", "priority": "high", "customer_id": None}
