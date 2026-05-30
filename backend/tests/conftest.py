import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from app.database import get_db


@pytest.fixture
def mock_db():
    """Async SQLAlchemy session mock with pre-wired awaitable methods."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def app_with_mock_db(mock_db):
    """FastAPI app with get_db overridden to yield the mock session."""

    async def override():
        yield mock_db

    app.dependency_overrides[get_db] = override
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_mock_db):
    """Async HTTP client wired directly to the FastAPI app (no network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_db), base_url="http://test"
    ) as c:
        yield c
