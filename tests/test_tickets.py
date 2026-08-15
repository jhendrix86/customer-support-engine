"""tickets.py is now real: every endpoint reads/writes tickets/customers/agents."""

from datetime import datetime

import pytest


async def _create_ticket(client, **overrides):
    payload = {"customer_name": "John Doe", "customer_email": "john@example.com", "subject": "Payment issue", "message": "My payment failed"}
    payload.update(overrides)
    r = await client.post("/tickets/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def _create_agent(client, **overrides):
    payload = {"name": "Alice Johnson", "email": "alice@example.com"}
    payload.update(overrides)
    r = await client.post("/agents/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_ticket_persists_a_real_row(client):
    body = await _create_ticket(client)
    assert body["subject"] == "Payment issue"
    assert body["status"] == "open"
    assert body["customer_email"] == "john@example.com"
    assert body["id"]  # a real generated UUID, not "ticket_123"


async def test_create_ticket_gets_or_creates_customer_by_email(client):
    a = await _create_ticket(client, customer_email="same@example.com")
    b = await _create_ticket(client, customer_email="same@example.com")
    assert a["customer_id"] == b["customer_id"]


async def test_create_ticket_requires_declared_fields(client):
    r = await client.post("/tickets/create", json={"subject": "x"})
    assert r.status_code == 422


async def test_sla_deadline_matches_priority_critical(client):
    body = await _create_ticket(client, priority="critical")
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(1 * 3600, abs=1)


async def test_sla_deadline_matches_priority_low(client):
    body = await _create_ticket(client, priority="low")
    created = datetime.fromisoformat(body["created_at"])
    deadline = datetime.fromisoformat(body["sla_deadline"])
    assert (deadline - created).total_seconds() == pytest.approx(48 * 3600, abs=1)


async def test_resolve_ticket_updates_the_real_row(client):
    ticket = await _create_ticket(client)
    r = await client.post(f"/tickets/{ticket['id']}/resolve", json={"resolution_notes": "Refunded"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "resolved"
    assert body["resolution_notes"] == "Refunded"


async def test_resolve_unknown_ticket_is_a_real_404(client):
    r = await client.post("/tickets/00000000-0000-0000-0000-000000000000/resolve", json={"resolution_notes": "x"})
    assert r.status_code == 404


async def test_escalate_ticket_updates_the_real_row(client):
    ticket = await _create_ticket(client)
    r = await client.post(f"/tickets/{ticket['id']}/escalate")
    assert r.status_code == 200
    assert r.json()["status"] == "escalated"


async def test_assign_ticket_to_a_real_agent(client):
    ticket = await _create_ticket(client)
    agent = await _create_agent(client)

    r = await client.post(f"/tickets/{ticket['id']}/assign", json={"agent_id": agent["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["assigned_agent_id"] == agent["id"]
    assert body["status"] == "in_progress"


async def test_assign_ticket_to_unknown_agent_is_a_real_404(client):
    ticket = await _create_ticket(client)
    r = await client.post(f"/tickets/{ticket['id']}/assign", json={"agent_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404


async def test_get_ticket_returns_the_real_row(client):
    ticket = await _create_ticket(client)
    r = await client.get(f"/tickets/{ticket['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == ticket["id"]


async def test_get_unknown_ticket_is_a_real_404(client):
    r = await client.get("/tickets/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_tickets_filters_by_priority_for_real(client):
    await _create_ticket(client, priority="critical", subject="crit-one")
    await _create_ticket(client, priority="low", subject="low-one")

    r = await client.get("/tickets/", params={"priority": "critical"})
    body = r.json()
    assert body["total"] == 1
    assert body["tickets"][0]["subject"] == "crit-one"
