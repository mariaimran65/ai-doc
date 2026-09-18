import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routes import health, auth
from app.chat import router as chat_router
from app.agents import router as agents_router
from app.knowledge import router as knowledge_router
from app.metrics import router as metrics_router

logger = logging.getLogger(__name__)

app = FastAPI(title="AI-Doc API", version="0.1.0")


@app.on_event("startup")
async def check_db() -> None:
    import socket
    from app.database import _db_host, _db_port

    host = _db_host
    port = int(_db_port)
    try:
        ip = socket.gethostbyname(host)
        logger.info("DB hostname '%s' resolves to IP: %s", host, ip)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            logger.info("DB raw TCP connect to %s:%s — OK", ip, port)
        else:
            logger.error(
                "DB raw TCP connect to %s:%s — FAILED (errno %s)", ip, port, result
            )
    except Exception as exc:
        logger.error("DB hostname '%s' resolution failed: %s", host, exc)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("DB connectivity check: OK")
    except Exception as exc:
        logger.error("DB connectivity check: FAILED — %s", exc)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(chat_router.router, prefix="/chat")
app.include_router(agents_router.router, prefix="/agents")
app.include_router(knowledge_router.router, prefix="/knowledge")
app.include_router(metrics_router.router, prefix="/metrics")
