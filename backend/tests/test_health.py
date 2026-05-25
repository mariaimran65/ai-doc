"""Tests for the /health endpoint."""
from httpx import AsyncClient, ASGITransport
from main import app


async def test_health_returns_ok():
    """GET /health must return 200 with status ok — no database required."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
