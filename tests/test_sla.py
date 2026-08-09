"""sla.py is 100% mock - see tests/test_tickets.py's module docstring."""


async def test_get_sla_status(client):
    r = await client.get("/sla/status")
    assert r.status_code == 200
    body = r.json()
    assert body["total_tickets"] == body["tickets_within_sla"] + body["tickets_approaching_sla"] + body["tickets_past_sla"]


async def test_get_sla_violations(client):
    r = await client.get("/sla/violations")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["violations"])


async def test_get_sla_violations_pagination_echoed(client):
    r = await client.get("/sla/violations", params={"limit": 10, "offset": 20})
    assert r.status_code == 200
    assert r.json()["pagination"] == {"limit": 10, "offset": 20}


async def test_escalate_sla_violation(client):
    r = await client.post("/sla/escalate/ticket_123")
    assert r.status_code == 200
    assert r.json()["escalated"] is True
