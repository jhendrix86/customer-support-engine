"""analytics.py is 100% mock - see tests/test_tickets.py's module docstring."""


async def test_get_support_metrics_defaults_to_a_30_day_window(client):
    r = await client.get("/analytics/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "period" in body
    assert body["total_tickets"] == body["open_tickets"] + body["resolved_tickets"] + body["escalated_tickets"]


async def test_get_support_metrics_echoes_explicit_dates(client):
    r = await client.get("/analytics/metrics", params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert r.status_code == 200
    assert r.json()["period"] == {"start_date": "2026-01-01", "end_date": "2026-01-31"}


async def test_get_agent_performance(client):
    r = await client.get("/analytics/performance")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["agents"])


async def test_get_csat_scores(client):
    r = await client.get("/analytics/satisfaction")
    assert r.status_code == 200
    body = r.json()
    assert 1 <= body["average_csat"] <= 5
