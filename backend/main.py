from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, auth
from app.chat import router as chat_router
from app.agents import router as agents_router
from app.knowledge import router as knowledge_router
from app.metrics import router as metrics_router

app = FastAPI(title="AI-Doc API", version="0.1.0")

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
