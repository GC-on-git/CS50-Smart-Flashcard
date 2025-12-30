"""
Script to load MCQ demo data from JSON file into the database
Usage: python cs50/backend/scripts/load_demo_data_mcq.py [user_email] [user_password]
"""
import sys
import json
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parents[1]  # Goes up to cs50/backend/
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.crud_users import create_user, get_user_by_email
from app.services.crud_decks import create_deck
from app.services.crud_cards import create_card
from app.auth.password_utils import hash_password
from app.schemas.deck import DeckCreate
from app.schemas.card import CardCreate, CardOptionCreate


def load_demo_data(user_email: str = "demo@example.com", user_password: str = "demopassword123"):
    """
    Load MCQ demo data from demo_data_mcq.json into the database.
    
    Args:
        user_email: Email for the demo user (will be created if doesn't exist)
        user_password: Password for the demo user
    """
    # Load demo data from JSON
    demo_file = Path(__file__).parent / "demo_data_mcq.json"
    with open(demo_file, 'r', encoding='utf-8') as f:
        demo_data = json.load(f)
    
    db: Session = SessionLocal()
    
    try:
        # Check if user exists, create if not
        print(f"Checking for user: {user_email}")
        user = get_user_by_email(db, user_email)
        
        if not user:
            print(f"Creating demo user: {user_email}")
            user = create_user(
                db=db,
                email=user_email,
                username=user_email.split('@')[0],
                hashed_password=hash_password(user_password)
            )
            print(f"Created user: {user.email} (ID: {user.id})")
        else:
            print(f"User already exists: {user.email} (ID: {user.id})")
        
        # Create decks and cards
        total_decks = 0
        total_cards = 0
        
        for deck_data in demo_data["decks"]:
            print(f"\nCreating deck: {deck_data['title']}")
            deck = create_deck(
                db=db,
                deck=DeckCreate(
                    title=deck_data["title"],
                    description=deck_data.get("description")
                ),
                user_id=user.id
            )
            total_decks += 1
            print(f"  Created deck: {deck.title} (ID: {deck.id})")
            
            # Create cards for this deck
            for card_data in deck_data["cards"]:
                # Convert options to CardOptionCreate format
                options = [
                    CardOptionCreate(text=opt["text"], is_correct=opt["is_correct"])
                    for opt in card_data["options"]
                ]
                
                card = create_card(
                    db=db,
                    card=CardCreate(
                        front=card_data["question"],
                        explanation=card_data.get("explanation", ""),
                        options=options
                    ),
                    deck_id=deck.id,
                    user_id=user.id
                )
                total_cards += 1
                print(f"    Created card: {card.front[:50]}...")
        
        print(f"\n{'='*60}")
        print(f"Demo data loaded successfully!")
        print(f"{'='*60}")
        print(f"User: {user_email}")
        print(f"Password: {user_password}")
        print(f"Total decks created: {total_decks}")
        print(f"Total cards created: {total_cards}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nError loading demo data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Allow custom user credentials via command line
    user_email = sys.argv[1] if len(sys.argv) > 1 else "demo@example.com"
    user_password = sys.argv[2] if len(sys.argv) > 2 else "demopassword123"
    
    load_demo_data(user_email, user_password)

