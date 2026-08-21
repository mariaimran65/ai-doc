"""Tests for the /agents endpoint.

Covers authentication guards, input validation, and the SSE streaming path.
The LangGraph graph is mocked so these tests run without hitting the
Anthropic API.

Router internals (what the mock must match):
  - build_graph() returns a graph
  - graph.stream(initial_state) is iterable; each item is {node_name: node_output}
  - node_output has keys "steps" (list) and "final_output" (str)
  - SSE events: {"step": <step_dict>} per step, then {"final": <str>}, then [DONE]
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

    graph.stream() returns an iterable of {node_name: node_output} dicts.
    The router collects steps from each node_output["steps"] and the final
    output from the last node_output["final_output"].
    SSE event keys: {"step": ...} per step, {"final": ...} for the output.
    """
    mock_stream_chunks = [
        {
            "supervisor": {
                "steps": [{"node": "supervisor", "output": "routing to researcher"}],
                "final_output": "",
            }
        },
        {
            "researcher": {
                "steps": [{"node": "researcher", "output": "found some results"}],
                "final_output": "Here is the final answer.",
            }
        },
    ]

    with patch("app.agents.router.build_graph") as mock_build:
        mock_graph = mock_build.return_value
        mock_graph.stream.return_value = iter(mock_stream_chunks)

        response = await client.post(
            "/agents/run",
            json={"task": "research LangGraph supervisor pattern"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = [
        line[5:].strip()
        for line in response.text.splitlines()
        if line.startswith("data:") and line[5:].strip() not in ("[DONE]", "")
    ]
    assert len(events) > 0

    parsed = [json.loads(e) for e in events]
    has_step = any("step" in e for e in parsed)
    has_final = any("final" in e for e in parsed)
    assert has_step
    assert has_final


async def test_agents_surfaces_error_in_stream(client, auth_cookies):
    """If the graph raises, the SSE stream must contain an error event."""
    with patch("app.agents.router.build_graph") as mock_build:
        mock_graph = mock_build.return_value
        mock_graph.stream.side_effect = RuntimeError("graph failure")

        response = await client.post(
            "/agents/run",
            json={"task": "some task"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "error" in response.text
