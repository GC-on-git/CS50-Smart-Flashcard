"""
FastAPI MVP - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import routes as auth
from app.routers import users, decks, cards

app = FastAPI(
    title="FastAPI MVP",
    description="Smart Flashcard Application with Spaced Repetition",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api/v1 prefix for API versioning
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(decks.router, prefix="/api/v1")
app.include_router(cards.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI MVP - Smart Flashcard Application"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

