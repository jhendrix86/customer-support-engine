"""knowledge_base.py is now real: articles hit the knowledge_articles table, search is a real ilike/term-overlap query."""


async def _create_article(client, **overrides):
    payload = {"title": "Payment Processing Troubleshooting", "content": "Check your payment method validity and available funds"}
    payload.update(overrides)
    r = await client.post("/kb/articles", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_article_persists_a_real_row(client):
    body = await _create_article(client)
    assert body["title"] == "Payment Processing Troubleshooting"
    assert body["view_count"] == 0
    assert body["id"]


async def test_search_with_no_matching_articles_is_honestly_empty(client):
    r = await client.post("/kb/search", json={"query": "quantum teleportation"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["articles"] == []


async def test_search_finds_real_matching_articles(client):
    await _create_article(client, title="Payment Troubleshooting", content="Check your payment method")
    await _create_article(client, title="Shipping Delays", content="Track your package status")

    r = await client.post("/kb/search", json={"query": "payment method"})
    body = r.json()
    assert body["total"] == 1
    assert body["articles"][0]["title"] == "Payment Troubleshooting"
    assert body["articles"][0]["relevance"] > 0


async def test_get_article_returns_the_real_row_and_increments_view_count(client):
    article = await _create_article(client)

    r = await client.get(f"/kb/articles/{article['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == article["id"]
    assert body["view_count"] == 1

    r2 = await client.get(f"/kb/articles/{article['id']}")
    assert r2.json()["view_count"] == 2


async def test_get_unknown_article_is_a_real_404(client):
    r = await client.get("/kb/articles/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_suggest_articles_for_a_real_ticket(client):
    await _create_article(client, title="Payment Troubleshooting", content="Check your payment method")

    ticket = (await client.post("/tickets/create", json={
        "customer_name": "John", "customer_email": "john@example.com",
        "subject": "Payment problem", "message": "My payment method is not working",
    })).json()

    r = await client.post(f"/kb/suggest/{ticket['id']}")
    assert r.status_code == 200
    assert len(r.json()["suggestions"]) >= 1


async def test_suggest_articles_for_unknown_ticket_is_a_real_404(client):
    r = await client.post("/kb/suggest/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
