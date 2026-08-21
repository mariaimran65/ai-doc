"""Tests for the /knowledge endpoint.

Covers authentication guards, file-type validation, document listing, and
the SSE Q&A streaming path. The LangChain ingest and retrieval calls are
mocked so these tests run without a database or Anthropic API key.
"""

import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------


async def test_upload_requires_auth(client):
    """POST /knowledge/upload without a JWT cookie must return 401."""
    response = await client.post(
        "/knowledge/upload",
        files={"file": ("test.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 401


async def test_list_docs_requires_auth(client):
    """GET /knowledge/documents without a JWT cookie must return 401."""
    response = await client.get("/knowledge/documents")
    assert response.status_code == 401


async def test_ask_requires_auth(client):
    """POST /knowledge/ask without a JWT cookie must return 401."""
    response = await client.post("/knowledge/ask", json={"question": "what is RAG?"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------


async def test_upload_rejects_unsupported_filetype(client, auth_cookies, mock_db):
    """Uploading a .csv file must return 400 — only PDF and .txt are accepted."""
    response = await client.post(
        "/knowledge/upload",
        files={"file": ("data.csv", BytesIO(b"a,b,c"), "text/csv")},
        cookies=auth_cookies,
    )
    assert response.status_code == 400
    assert "Only PDF" in response.json()["detail"]


async def test_upload_rejects_oversized_file(client, auth_cookies, mock_db):
    """Files larger than 10 MB must be rejected with 400."""
    big_content = b"x" * (10 * 1024 * 1024 + 1)
    response = await client.post(
        "/knowledge/upload",
        files={"file": ("big.txt", BytesIO(big_content), "text/plain")},
        cookies=auth_cookies,
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Upload success (mocked ingest)
# ---------------------------------------------------------------------------


async def test_upload_txt_succeeds(client, auth_cookies, mock_db):
    """Uploading a valid .txt file must call ingest_document and return 200."""
    mock_result = {"document_id": "abc-123", "chunks": 5, "filename": "notes.txt"}

    with patch(
        "app.knowledge.router.ingest_document", new_callable=AsyncMock
    ) as mock_ingest:
        mock_ingest.return_value = mock_result

        response = await client.post(
            "/knowledge/upload",
            files={"file": ("notes.txt", BytesIO(b"some content"), "text/plain")},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "abc-123"
    assert body["chunks"] == 5
    mock_ingest.assert_called_once()


# ---------------------------------------------------------------------------
# Document listing
# ---------------------------------------------------------------------------


async def test_list_docs_returns_empty_list(client, auth_cookies, mock_db):
    """GET /knowledge/documents with no documents must return an empty list."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result

    response = await client.get("/knowledge/documents", cookies=auth_cookies)
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Q&A streaming
# ---------------------------------------------------------------------------


async def test_ask_streams_sse_answer(client, auth_cookies, mock_db):
    """POST /knowledge/ask must stream an SSE answer from the retrieval chain."""
    with patch(
        "app.knowledge.router.answer_question", new_callable=AsyncMock
    ) as mock_answer:
        mock_answer.return_value = "RAG stands for Retrieval-Augmented Generation."

        response = await client.post(
            "/knowledge/ask",
            json={"question": "what is RAG?"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "data:" in body
    assert "[DONE]" in body

    # Tokens should reconstruct the answer
    tokens = []
    for line in body.splitlines():
        if line.startswith("data:") and "[DONE]" not in line:
            try:
                tokens.append(json.loads(line[5:].strip()).get("token", ""))
            except json.JSONDecodeError:
                pass
    assert "RAG" in "".join(tokens)


async def test_ask_surfaces_error_in_stream(client, auth_cookies, mock_db):
    """If answer_question raises, the SSE stream must contain an error event."""
    with patch(
        "app.knowledge.router.answer_question", new_callable=AsyncMock
    ) as mock_answer:
        mock_answer.side_effect = RuntimeError("DB unavailable")

        response = await client.post(
            "/knowledge/ask",
            json={"question": "what happened?"},
            cookies=auth_cookies,
        )

    assert response.status_code == 200
    assert "error" in response.text
