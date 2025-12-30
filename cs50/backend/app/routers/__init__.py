"""
API routers
"""
from app.routers.users import router as users_router
from app.routers.decks import router as decks_router
from app.routers.cards import router as cards_router
from app.routers.preferences import router as preferences_router
from app.routers.statistics import router as statistics_router

__all__ = ["users_router", "decks_router", "cards_router", "preferences_router", "statistics_router"]
