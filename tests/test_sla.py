"""sla.py is now real: every endpoint computes from actual tickets, and /escalate delivers a real notification-engine call."""

import httpx
import respx


async def _create_ticket(client, **overrides):
    payload = {"customer_name": "John Doe", "customer_email": "john@example.com", "subject": "Payment issue", "message": "My payment failed", "priority": "critical"}
    payload.update(overrides)
    return (await client.post("/tickets/create", json=payload)).json()


async def test_sla_status_with_no_tickets_is_honestly_empty(client):
    r = await client.get("/sla/status")
    assert r.status_code == 200
    body = r.json()
    assert body["total_tickets"] == 0
    assert body["sla_compliance_rate"] is None


async def test_sla_status_reflects_real_tickets(client):
    await _create_ticket(client)
    r = await client.get("/sla/status")
    body = r.json()
    assert body["total_tickets"] == 1
    assert body["tickets_within_sla"] == 1
    assert body["sla_compliance_rate"] == 100.0


async def test_sla_violations_is_honestly_empty_with_nothing_overdue(client):
    await _create_ticket(client, priority="low")
    r = await client.get("/sla/violations")
    assert r.status_code == 200
    assert r.json()["total"] == 0


async def test_sla_violations_finds_a_real_overdue_resolved_ticket(client, db_session):
    from datetime import datetime, timedelta
    from app.models.ticket import Ticket, TicketStatus

    ticket = await _create_ticket(client)
    result = await db_session.get(Ticket, __import__("uuid").UUID(ticket["id"]))
    result.status = TicketStatus.RESOLVED
    result.resolved_at = datetime.utcnow() + timedelta(hours=5)  # after its 1h critical deadline
    result.sla_violated = True
    await db_session.commit()

    r = await client.get("/sla/violations")
    body = r.json()
    assert body["total"] == 1
    assert body["violations"][0]["ticket_id"] == ticket["id"]


@respx.mock
async def test_escalate_sla_violation_delivers_a_real_notification(client):
    respx.post("http://localhost:8037/notifications/send").mock(return_value=httpx.Response(200, json={"status": "sent"}))

    ticket = await _create_ticket(client)
    r = await client.post(f"/sla/escalate/{ticket['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["escalated"] is True
    assert body["notified"] is True

    updated = (await client.get(f"/tickets/{ticket['id']}")).json()
    assert updated["status"] == "escalated"


async def test_escalate_sla_violation_reports_honest_failure_when_notification_engine_unreachable(client):
    ticket = await _create_ticket(client)
    r = await client.post(f"/sla/escalate/{ticket['id']}")

    body = r.json()
    assert body["escalated"] is True  # ticket status change is real regardless
    assert body["notified"] is False
    assert body["notification_error"] is not None


async def test_escalate_unknown_ticket_is_a_real_404(client):
    r = await client.post("/sla/escalate/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
