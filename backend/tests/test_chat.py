"""Tests for the /chat endpoint.

Covers authentication guards, input validation, and the SSE streaming path.
The LangChain agent and Redis calls are mocked so these tests run without
a live LLM API key or Redis instance.
"""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


async def test_chat_requires_auth(client):
    """POST /chat/ without a JWT cookie must return 401."""
    response = await client.post(
        "/chat/", json={"messages": [{"role": "user", "content": "hello"}]}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


async def test_chat_rejects_empty_messages(client, auth_cookies):
    """POST /chat/ with an empty messages list must return 400."""
    response = await client.post("/chat/", json={"messages": []}, cookies=auth_cookies)
    assert response.status_code == 400


async def test_chat_rejects_missing_messages_field(client, auth_cookies):
    """POST /chat/ with no messages field must return 422 (Pydantic validation)."""
    response = await client.post("/chat/", json={}, cookies=auth_cookies)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Streaming response
# ---------------------------------------------------------------------------


async def test_chat_streams_sse_tokens(client, auth_cookies):
    """POST /chat/ with a valid message must stream SSE tokens back.

    The agent chain is mocked to return a fixed output so we can assert
    the SSE format without hitting the Anthropic API or Redis.
    """
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"output": "Hello from the assistant!"}

    with patch("app.chat.router.build_chain", return_value=mock_chain):
        response = await client.post(
            "/chat/",
            json={"messages": [{"role": "user", "content": "hi"}]},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    # The response must contain SSE data lines with tokens and a final [DONE]
    assert "data:" in body
    assert "[DONE]" in body


async def test_chat_surfaces_agent_error_in_stream(client, auth_cookies):
    """If the agent raises, the SSE stream must contain an error event (not a 500)."""
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = RuntimeError("LLM unavailable")

    with patch("app.chat.router.build_chain", return_value=mock_chain):
        response = await client.post(
            "/chat/",
            json={"messages": [{"role": "user", "content": "hi"}]},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "error" in response.text
