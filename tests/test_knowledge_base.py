"""knowledge_base.py is 100% mock - see tests/test_tickets.py's module docstring."""


async def test_search_knowledge_base(client):
    r = await client.post("/kb/search", json={"query": "payment failed"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "payment failed"
    assert body["total"] == len(body["articles"])


async def test_search_requires_query(client):
    r = await client.post("/kb/search", json={})
    assert r.status_code == 422


async def test_suggest_articles(client):
    r = await client.post("/kb/suggest/ticket_123")
    assert r.status_code == 200
    assert r.json()["ticket_id"] == "ticket_123"


async def test_get_article(client):
    r = await client.get("/kb/articles/kb_001")
    assert r.status_code == 200
    assert r.json()["id"] == "kb_001"
