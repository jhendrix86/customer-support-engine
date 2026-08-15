"""agents.py is new this session - real CRUD, needed for /tickets/{id}/assign to ever work against something real."""


async def test_create_agent_persists_a_real_row(client):
    r = await client.post("/agents/create", json={"name": "Alice Johnson", "email": "alice@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Alice Johnson"
    assert body["status"] == "available"
    assert body["id"]


async def test_get_unknown_agent_is_a_real_404(client):
    r = await client.get("/agents/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_agents_reflects_real_created_rows(client):
    await client.post("/agents/create", json={"name": "one", "email": "one@example.com"})
    await client.post("/agents/create", json={"name": "two", "email": "two@example.com"})

    r = await client.get("/agents/")
    body = r.json()
    assert body["total"] == 2
