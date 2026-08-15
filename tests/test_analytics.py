"""analytics.py is now real: every endpoint computes from actual Ticket/Agent/Customer/Response data."""


async def _create_ticket(client, **overrides):
    payload = {"customer_name": "John Doe", "customer_email": "john@example.com", "subject": "Payment issue", "message": "My payment failed"}
    payload.update(overrides)
    return (await client.post("/tickets/create", json=payload)).json()


async def test_metrics_with_no_tickets_is_honestly_empty(client):
    r = await client.get("/analytics/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["total_tickets"] == 0
    assert body["first_contact_resolution_rate"] is None


async def test_metrics_reflects_real_tickets(client):
    await _create_ticket(client, priority="critical", channel="chat")
    await _create_ticket(client, priority="low", channel="email")

    r = await client.get("/analytics/metrics")
    body = r.json()
    assert body["total_tickets"] == 2
    assert body["open_tickets"] == 2
    assert body["by_priority"]["critical"]["count"] == 1
    assert body["by_channel"]["chat"]["count"] == 1


async def test_performance_with_no_agents_is_honestly_empty(client):
    r = await client.get("/analytics/performance")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "agents": []}


async def test_performance_aggregates_real_assigned_tickets(client):
    agent = (await client.post("/agents/create", json={"name": "Alice", "email": "alice@example.com"})).json()
    ticket = await _create_ticket(client)
    await client.post(f"/tickets/{ticket['id']}/assign", json={"agent_id": agent["id"]})

    r = await client.get("/analytics/performance")
    body = r.json()
    assert body["total"] == 1
    assert body["agents"][0]["agent_name"] == "Alice"
    assert body["agents"][0]["tickets_handled"] == 1


async def test_satisfaction_with_no_scores_is_honestly_empty(client):
    r = await client.get("/analytics/satisfaction")
    assert r.status_code == 200
    body = r.json()
    assert body["total_surveys"] == 0
    assert body["average_csat"] is None


async def test_satisfaction_aggregates_real_csat_scores(client, db_session):
    import uuid
    from app.models.ticket import Ticket

    ticket = await _create_ticket(client)
    row = await db_session.get(Ticket, uuid.UUID(ticket["id"]))
    row.csat_score = 5
    await db_session.commit()

    r = await client.get("/analytics/satisfaction")
    body = r.json()
    assert body["total_surveys"] == 1
    assert body["average_csat"] == 5.0
    assert body["by_score"]["5"] == 1
