"""ai_responses.py is 100% mock - see tests/test_tickets.py's module docstring."""


async def test_generate_ai_response(client):
    r = await client.post("/ai/generate-response", json={
        "ticket_id": "ticket_123", "customer_message": "My payment failed",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ticket_id"] == "ticket_123"
    assert "response" in body


async def test_generate_ai_response_requires_ticket_id(client):
    r = await client.post("/ai/generate-response", json={"customer_message": "Help"})
    assert r.status_code == 422


async def test_send_ai_response(client):
    r = await client.post("/ai/respond/ticket_123")
    assert r.status_code == 200
    assert r.json()["status"] == "sent"


async def test_get_suggestions(client):
    r = await client.get("/ai/suggestions/ticket_123")
    assert r.status_code == 200
    assert r.json()["ticket_id"] == "ticket_123"
    assert isinstance(r.json()["suggestions"], list)
