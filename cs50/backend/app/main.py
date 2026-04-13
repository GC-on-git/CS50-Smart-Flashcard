"""
FastAPI MVP - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import routes as auth
from app.core.config import settings
from app.routers import users, decks, cards, preferences, statistics

app = FastAPI(
    title="FastAPI MVP",
    description="Smart Flashcard Application with Spaced Repetition",
    version="1.0.0"
)

allowed_origins = [o.strip() for o in (settings.ALLOWED_ORIGINS or "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(decks.router, prefix="/api/v1")
app.include_router(cards.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI MVP - Smart Flashcard Application"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

