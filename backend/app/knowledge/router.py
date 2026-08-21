import asyncio
import json

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.auth_utils import get_current_user
from app.database import get_db
from app.knowledge.ingest import ingest_document
from app.knowledge.retrieval import answer_question

router = APIRouter()


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload and ingest a PDF or text file."""
    if file.content_type not in ("application/pdf", "text/plain"):
        raise HTTPException(
            status_code=400, detail="Only PDF and .txt files are supported."
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB).")

    try:
        result = await ingest_document(
            db=db,
            user_id=current_user["sub"],
            filename=file.filename or "upload",
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all documents uploaded by the current user."""
    rows = await db.execute(
        text(
            "SELECT id, title, source_name, created_at, "
            "(SELECT COUNT(*) FROM document_chunks WHERE document_id = documents.id) AS chunks "
            "FROM documents WHERE user_id = :uid ORDER BY created_at DESC"
        ),
        {"uid": current_user["sub"]},
    )
    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "source_name": r[2],
            "created_at": str(r[3]),
            "chunks": r[4],
        }
        for r in rows.fetchall()
    ]


class AskRequest(BaseModel):
    question: str
    document_id: str | None = None


@router.post("/ask")
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Answer a question using RAG — retrieves relevant chunks then generates with Claude."""

    async def event_generator():
        try:
            answer = await answer_question(
                db=db,
                question=body.question,
                document_id=body.document_id,
            )
            chunk_size = 4
            for i in range(0, len(answer), chunk_size):
                yield {"data": json.dumps({"token": answer[i : i + chunk_size]})}
                await asyncio.sleep(0.01)
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
