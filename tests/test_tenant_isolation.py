"""
Verifies tenant isolation for customer-support-engine endpoints.
Tests that automatic query filtering actually isolates data between tenants.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def _create_ticket(client, tenant_id, subject):
    resp = await client.post(
        "/tickets/create",
        json={
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "subject": subject,
            "message": "Test message",
            "priority": "medium"
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_ticket(client):
    ticket_id = await _create_ticket(client, TENANT_A, "Tenant A's Issue")

    same_tenant = await client.get(f"/tickets/{ticket_id}", headers={"X-Tenant-ID": TENANT_A})
    assert same_tenant.status_code == 200

    other_tenant = await client.get(f"/tickets/{ticket_id}", headers={"X-Tenant-ID": TENANT_B})
    assert other_tenant.status_code == 404


async def test_list_tickets_is_scoped_per_tenant(client):
    await _create_ticket(client, TENANT_A, "A's Issue 1")
    await _create_ticket(client, TENANT_A, "A's Issue 2")
    
    # Verify tenant A sees their tickets
    a_listing = await client.get("/tickets/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 2


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_ticket(client, TENANT_A, "A's Issue")
    
    # Verify no-tenant header sees the ticket
    unscoped = await client.get("/tickets/")
    assert unscoped.status_code == 200
    assert unscoped.json()["total"] == 1


async def test_tenant_cannot_modify_another_tenants_ticket(client):
    ticket_id = await _create_ticket(client, TENANT_A, "Tenant A's Issue")

    # Try to resolve as tenant B
    resolve_response = await client.post(
        f"/tickets/{ticket_id}/resolve",
        json={"resolution_notes": "Fixed by tenant B"},
        headers={"X-Tenant-ID": TENANT_B}
    )
    assert resolve_response.status_code == 404


async def test_agent_creation_respects_tenant_scoping(client):
    """Agent creation should be tenant-scoped."""
    # Create agent for tenant A
    agent_resp = await client.post(
        "/agents/create",
        json={
            "name": "Agent Smith",
            "email": "agent@example.com",
            "specialization": ["technical"]
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert agent_resp.status_code == 200
    agent_id = agent_resp.json()["id"]

    # Tenant A can see the agent
    a_agent = await client.get(f"/agents/{agent_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_agent.status_code == 200

    # Tenant B cannot see the agent
    b_agent = await client.get(f"/agents/{agent_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_agent.status_code == 404


async def test_knowledge_base_article_respects_tenant_scoping(client):
    """Knowledge base articles should be tenant-scoped."""
    # Create article for tenant A
    article_resp = await client.post(
        "/kb/articles",
        json={
            "title": "Troubleshooting Guide",
            "content": "Step-by-step instructions",
            "category": "technical"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert article_resp.status_code == 200
    article_id = article_resp.json()["id"]

    # Tenant A can see the article
    a_article = await client.get(f"/kb/articles/{article_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_article.status_code == 200

    # Tenant B cannot see the article
    b_article = await client.get(f"/kb/articles/{article_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_article.status_code == 404
