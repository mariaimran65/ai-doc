import asyncio

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sse_starlette.sse import AppStatus

from main import app
from app.database import get_db
from app.config import settings


@pytest.fixture(autouse=True)
async def reset_sse_app_status():
    # AppStatus.should_exit_event is a module-level asyncio.Event bound to
    # whichever loop first imported sse_starlette. pytest-asyncio creates a
    # fresh loop per test function, so the singleton would be from the wrong
    # loop and raise "bound to a different event loop" in every SSE test.
    # Re-creating it here (inside an async fixture) binds it to this test's loop.
    AppStatus.should_exit = False
    AppStatus.should_exit_event = asyncio.Event()
    yield


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


@pytest.fixture
def auth_cookies():
    """Generate a valid JWT access_token cookie for authenticated test requests."""
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "session_token": "test-session-token",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return {"access_token": token}
