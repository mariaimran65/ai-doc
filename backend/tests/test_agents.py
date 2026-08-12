"""Tests for the /agents endpoint.

Covers authentication guards, input validation, and the SSE streaming path.
The LangGraph graph is mocked so these tests run without hitting the
Anthropic API.
"""

import json
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


async def test_agents_requires_auth(client):
    """POST /agents/run without a JWT cookie must return 401."""
    response = await client.post("/agents/run", json={"task": "research LangGraph"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


async def test_agents_rejects_empty_task(client, auth_cookies):
    """POST /agents/run with an empty task string must return 400."""
    response = await client.post("/agents/run", json={"task": ""}, cookies=auth_cookies)
    assert response.status_code == 400


async def test_agents_rejects_missing_task(client, auth_cookies):
    """POST /agents/run with no task field must return 422 (Pydantic validation)."""
    response = await client.post("/agents/run", json={}, cookies=auth_cookies)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Streaming response
# ---------------------------------------------------------------------------


async def test_agents_streams_steps_and_output(client, auth_cookies):
    """POST /agents/run must stream step events followed by the final output.

    The LangGraph graph is mocked to return a fixed state so we can assert
    the SSE event structure without hitting the Anthropic API.
    """
    mock_result = {
        "steps": [
            {"node": "supervisor", "output": "routing to researcher"},
            {"node": "researcher", "output": "found some results"},
            {"node": "summariser", "output": "synthesised output"},
        ],
        "final_output": "Here is the final answer.",
    }

    with patch("app.agents.router.build_graph") as mock_build:
        mock_graph = mock_build.return_value
        mock_graph.invoke.return_value = mock_result

        response = await client.post(
            "/agents/run",
            json={"task": "research LangGraph supervisor pattern"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Parse SSE events from the body
    events = [
        line[5:].strip()
        for line in response.text.splitlines()
        if line.startswith("data:") and line[5:].strip() not in ("[DONE]", "")
    ]
    assert len(events) > 0

    # At least one step event and one output event must be present
    parsed = [json.loads(e) for e in events]
    has_step = any("step" in e for e in parsed)
    has_output = any("output" in e for e in parsed)
    assert has_step
    assert has_output


async def test_agents_surfaces_error_in_stream(client, auth_cookies):
    """If the graph raises, the SSE stream must contain an error event."""
    with patch("app.agents.router.build_graph") as mock_build:
        mock_graph = mock_build.return_value
        mock_graph.invoke.side_effect = RuntimeError("graph failure")

        response = await client.post(
            "/agents/run",
            json={"task": "some task"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "error" in response.text
