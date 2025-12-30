"""
Service layer / CRUD operations
"""
from app.services.crud_users import (
    get_user_by_id, get_user_by_email, get_user_by_username,
    create_user, update_user, get_users
)
from app.services.crud_decks import (
    get_deck, get_decks, create_deck, update_deck, delete_deck
)
from app.services.crud_cards import (
    get_card, get_cards, create_card, update_card, delete_card,
    review_card, get_due_cards, get_due_cards_count
)
from app.services.scheduling import (
    calculate_sm2_update, update_card_schedule,
    get_cards_due_for_review, get_cards_due_count
)

__all__ = [
    "get_user_by_id", "get_user_by_email", "get_user_by_username",
    "create_user", "update_user", "get_users",
    "get_deck", "get_decks", "create_deck", "update_deck", "delete_deck",
    "get_card", "get_cards", "create_card", "update_card", "delete_card",
    "review_card", "get_due_cards", "get_due_cards_count",
    "calculate_sm2_update", "update_card_schedule",
    "get_cards_due_for_review",
]
