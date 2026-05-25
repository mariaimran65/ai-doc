from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes import health, auth

app = FastAPI(title="AI-Doc API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
