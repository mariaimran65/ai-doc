from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.auth_utils import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("/")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return platform-wide usage statistics from the database."""

    counts = await db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM users)                                    AS total_users,
                (SELECT COUNT(*) FROM documents)                                AS total_documents,
                (SELECT COUNT(*) FROM document_chunks)                          AS total_chunks,
                (SELECT COUNT(*) FROM pipeline_runs)                            AS total_runs,
                (SELECT COUNT(*) FROM pipeline_runs WHERE status = 'completed') AS completed_runs,
                (SELECT COUNT(*) FROM sessions WHERE expires_at > now())        AS active_sessions
        """)
    )
    row = counts.fetchone()

    recent = await db.execute(
        text("""
            SELECT user_id, email, name, provider, signed_in_at
            FROM active_sessions
            LIMIT 10
        """)
    )
    recent_signins = [
        {
            "email": r[1],
            "name": r[2],
            "provider": r[3],
            "signed_in_at": str(r[4]),
        }
        for r in recent.fetchall()
    ]

    runs = await db.execute(
        text("""
            SELECT id, triggered_by, task, started_at, duration_seconds
            FROM completed_pipeline_runs
            LIMIT 10
        """)
    )
    recent_runs = [
        {
            "id": str(r[0]),
            "triggered_by": r[1],
            "task": r[2],
            "started_at": str(r[3]),
            "duration_seconds": float(r[4]) if r[4] is not None else None,
        }
        for r in runs.fetchall()
    ]

    return {
        "counts": {
            "users": row[0],
            "documents": row[1],
            "chunks": row[2],
            "total_runs": row[3],
            "completed_runs": row[4],
            "active_sessions": row[5],
        },
        "recent_signins": recent_signins,
        "recent_runs": recent_runs,
    }
