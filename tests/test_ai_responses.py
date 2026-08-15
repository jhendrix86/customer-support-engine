"""ai_responses.py is now real: OpenAI-backed drafting (honest failure when unconfigured) and real KB suggestions."""


async def _create_ticket(client, **overrides):
    payload = {"customer_name": "John Doe", "customer_email": "john@example.com", "subject": "Payment issue", "message": "My payment failed"}
    payload.update(overrides)
    return (await client.post("/tickets/create", json=payload)).json()


async def test_generate_ai_response_without_openai_configured_reports_honest_failure(client):
    # Force the unconfigured state explicitly - an OPENAI_API_KEY may be
    # set in the ambient environment on this machine, which would
    # otherwise make this a real (and unpredictable) network call.
    from app.main import app as fastapi_app
    fastapi_app.state.ai_responder._client = None

    ticket = await _create_ticket(client)

    r = await client.post("/ai/generate-response", json={"ticket_id": ticket["id"], "customer_message": "Help!"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "not configured" in body["error"]
    assert body["response"] is None


async def test_generate_ai_response_for_unknown_ticket_is_a_real_404(client):
    r = await client.post("/ai/generate-response", json={"ticket_id": "00000000-0000-0000-0000-000000000000", "customer_message": "Help!"})
    assert r.status_code == 404


async def test_generate_ai_response_with_a_fake_client_returns_real_kb_matches(client):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    await client.post("/kb/articles", json={"title": "Payment Troubleshooting", "content": "Check your payment method and available funds"})

    from app.main import app as fastapi_app
    fake_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Please check your payment method."))])
    fastapi_app.state.ai_responder._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(return_value=fake_response)))
    )

    ticket = await _create_ticket(client, message="My payment method failed")
    r = await client.post("/ai/generate-response", json={"ticket_id": ticket["id"], "customer_message": "My payment method failed"})

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["response"] == "Please check your payment method."
    assert len(body["suggested_articles"]) >= 1


async def test_send_ai_response_without_openai_configured_reports_honest_failure(client):
    from app.main import app as fastapi_app
    fastapi_app.state.ai_responder._client = None

    ticket = await _create_ticket(client)
    r = await client.post(f"/ai/respond/{ticket['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "not configured" in body["error"]


async def test_send_ai_response_with_a_fake_client_persists_a_real_response(client):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.main import app as fastapi_app
    fake_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="We're on it!"))])
    fastapi_app.state.ai_responder._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(return_value=fake_response)))
    )

    ticket = await _create_ticket(client)
    r = await client.post(f"/ai/respond/{ticket['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["message"] == "We're on it!"
    assert body["response_type"] == "ai_generated"

    updated_ticket = (await client.get(f"/tickets/{ticket['id']}")).json()
    assert updated_ticket["status"] == "waiting_customer"


async def test_send_ai_response_for_unknown_ticket_is_a_real_404(client):
    r = await client.post("/ai/respond/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_get_suggestions_for_unknown_ticket_is_a_real_404(client):
    r = await client.get("/ai/suggestions/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_get_suggestions_returns_real_matching_articles(client):
    await client.post("/kb/articles", json={"title": "Refund Policy", "content": "Refunds are processed within 5 business days"})
    ticket = await _create_ticket(client, subject="Refund question", message="How do refunds work")

    r = await client.get(f"/ai/suggestions/{ticket['id']}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["suggestions"]) >= 1
    assert body["suggestions"][0]["title"] == "Refund Policy"
