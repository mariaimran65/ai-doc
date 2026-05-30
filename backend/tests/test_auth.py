"""Tests for OAuth callback behaviour and database constraints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.user import User


# ---------------------------------------------------------------------------
# OAuth callback — creates user
# ---------------------------------------------------------------------------


async def test_oauth_callback_creates_user(client, mock_db):
    """Callback with an unknown Google user must insert a new User row."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # user does not exist yet
    mock_db.execute.return_value = mock_result

    with patch("app.routes.auth.httpx.AsyncClient") as mock_httpx:
        instance = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = instance

        token_resp = MagicMock()
        token_resp.is_success = True
        token_resp.json.return_value = {"access_token": "fake-token"}
        instance.post = AsyncMock(return_value=token_resp)

        profile_resp = MagicMock()
        profile_resp.is_success = True
        profile_resp.json.return_value = {
            "id": "google-uid-001",
            "email": "new@example.com",
            "picture": "https://example.com/pic.jpg",
        }
        instance.get = AsyncMock(return_value=profile_resp)

        response = await client.get(
            "/auth/callback?code=testcode&state=teststate",
            follow_redirects=False,
        )

    assert response.status_code == 302
    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# OAuth callback — duplicate login updates existing record
# ---------------------------------------------------------------------------


async def test_duplicate_oauth_login_updates_existing_record(client, mock_db):
    """Callback for a returning user must update the existing row, not insert a new one."""
    existing_user = User(
        id=uuid.uuid4(),
        email="returning@example.com",
        provider="google",
        provider_user_id="google-uid-002",
        avatar_url="https://old-pic.example.com",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_db.execute.return_value = mock_result

    with patch("app.routes.auth.httpx.AsyncClient") as mock_httpx:
        instance = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = instance

        token_resp = MagicMock()
        token_resp.is_success = True
        token_resp.json.return_value = {"access_token": "fake-token"}
        instance.post = AsyncMock(return_value=token_resp)

        profile_resp = MagicMock()
        profile_resp.is_success = True
        profile_resp.json.return_value = {
            "id": "google-uid-002",
            "email": "returning@example.com",
            "picture": "https://new-pic.example.com",
        }
        instance.get = AsyncMock(return_value=profile_resp)

        response = await client.get(
            "/auth/callback?code=testcode&state=teststate",
            follow_redirects=False,
        )

    assert response.status_code == 302
    # The existing user's avatar was updated, no new row added
    assert existing_user.avatar_url == "https://new-pic.example.com"
    mock_db.add.assert_called_once()  # only the Session row, not a second User


# ---------------------------------------------------------------------------
# Unique constraint declared on the model
# ---------------------------------------------------------------------------


def test_unique_constraint_on_provider_and_provider_user_id():
    """User model must declare a UniqueConstraint on (provider, provider_user_id).

    This verifies the model mirrors the constraint defined in schema.sql so that
    SQLAlchemy will raise IntegrityError on a duplicate insert rather than
    silently creating a second identity row for the same Google account.
    """
    constraint_columns = {
        frozenset(col.name for col in c.columns)
        for c in User.__table__.constraints
        if hasattr(c, "columns")
    }
    assert frozenset({"provider", "provider_user_id"}) in constraint_columns


# ---------------------------------------------------------------------------
# /auth/me — unauthenticated request is rejected
# ---------------------------------------------------------------------------


async def test_me_returns_401_without_cookie(client):
    """GET /auth/me must return 401 when no JWT cookie is present."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
