"""
Card router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.card import (
    CardCreate, CardUpdate, CardResponse, CardReview, AICardGenerationRequest,
    CardStudyResponse, AnswerSubmission, AnswerResponse, CardOptionResponse,
    BulkDeleteRequest
)
from app.services.crud_cards import (
    get_card, get_cards, create_card, update_card, delete_card,
    review_card, get_due_cards, get_due_cards_count, submit_answer
)
from app.core.config import settings
from app.services.ai_generator import generate_cards_with_ai

router = APIRouter(prefix="/decks/{deck_id}/cards", tags=["cards"])

@router.post("/generate", response_model=List[CardResponse], status_code=status.HTTP_201_CREATED)
async def generate_cards_endpoint(
    deck_id: int,
    request: AICardGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate cards using AI based on a topic description.
    
    Creates multiple flashcards automatically using AI based on the provided topic.
    The cards will be added to the specified deck, which must be owned by the current user.
    
    Args:
        deck_id: Deck ID
        request: AI generation request (topic, num_cards)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CardResponse]: List of created cards
        
    Raises:
        HTTPException: If deck not found, AI generation fails, or AI_API_KEY not configured
    """
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    try:
        generated_cards = generate_cards_with_ai(
            topic=request.topic or "",
            num_cards=request.num_cards,
            deck_title=deck.title,
            deck_description=deck.description
        )
        
        created_cards = []
        for card_data in generated_cards:
            from app.schemas.card import CardOptionCreate
            options = [
                CardOptionCreate(text=opt["text"], is_correct=opt["is_correct"])
                for opt in card_data["options"]
            ]
            card_create = CardCreate(
                front=card_data["question"],
                explanation=card_data.get("explanation", ""),
                options=options
            )
            db_card = create_card(
                db=db,
                card=card_create,
                deck_id=deck_id,
                user_id=current_user.id
            )
            if db_card:
                created_cards.append(db_card)
        
        return created_cards
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cards: {str(e)}"
        )

@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_cards_endpoint(
    deck_id: int,
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk delete cards.
    
    Args:
        deck_id: Deck ID
        request: Bulk delete request with card_ids list
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    from app.services.crud_cards import bulk_delete_cards
    success = bulk_delete_cards(db, deck_id, request.card_ids, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or cards not found"
        )
    return None

@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card_endpoint(
    deck_id: int,
    card: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a new MCQ card to a deck.
    
    Creates a new flashcard with question, explanation, and options in the specified deck.
    The deck must be owned by the current authenticated user.
    
    Args:
        deck_id: Deck ID
        card: Card creation data (front/question, explanation, options)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Created card information
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    db_card = create_card(
        db=db,
        card=card,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return db_card

@router.get("", response_model=List[CardResponse])
async def list_cards(
    deck_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    query: Optional[str] = Query(None, description="Search query for front/back content"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all cards in a deck with optional search/filter.
    
    Returns a paginated list of cards in the specified deck.
    Supports filtering by front or back content using the query parameter.
    Only returns cards from decks owned by the current user.
    
    Args:
        deck_id: Deck ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        query: Optional search query to filter cards by front/back content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CardResponse]: List of card objects
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    cards = get_cards(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        query=query
    )
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck and not cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return cards

@router.get("/due", response_model=List[CardResponse])
async def get_due_cards_endpoint(
    deck_id: int,
    limit: int = Query(100, ge=1, le=100, description="Maximum number of cards to return"),
    mode: Optional[str] = Query(None, description="Study mode: 'hard' for cards with ease_factor < 2.0"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get cards that are due for review.
    
    Returns cards that have never been reviewed (next_review is None)
    or cards whose next_review date has passed.
    
    Args:
        deck_id: Deck ID
        limit: Maximum number of cards to return (1-100)
        mode: Optional study mode. 'hard' filters cards with ease_factor < 2.0
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CardResponse]: List of cards due for review
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    cards = get_due_cards(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id,
        limit=limit,
        mode=mode
    )
    
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    return cards

@router.get("/due/count")
async def get_due_cards_count_endpoint(
    deck_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the count of cards due for review in a deck.
    
    Args:
        deck_id: Deck ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Dictionary with count of due cards
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    count = get_due_cards_count(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id
    )
    
    return {"deck_id": deck_id, "due_count": count}

@router.post("/{card_id}/duplicate", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_card_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate a card.
    
    Creates a copy of the card with the same content and options.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID to duplicate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Duplicated card
        
    Raises:
        HTTPException: If card not found or not owned by user
    """
    from app.services.crud_cards import duplicate_card
    duplicated_card = duplicate_card(db, deck_id, card_id, current_user.id)
    if duplicated_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return duplicated_card

@router.get("/{card_id}", response_model=CardResponse)
async def get_card_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific card with options.
    
    Returns detailed information about a single card including all options.
    Only returns cards from decks owned by the current user.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Card information with options
        
    Raises:
        HTTPException: If card or deck not found or not owned by user
    """
    db_card = get_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    from app.models.card import CardOption
    options = db.query(CardOption).filter(CardOption.card_id == card_id).order_by(CardOption.order).all()
    
    card_response = CardResponse(
        id=db_card.id,
        deck_id=db_card.deck_id,
        front=db_card.front,
        explanation=db_card.explanation,
        created_at=db_card.created_at,
        updated_at=db_card.updated_at,
        ease_factor=db_card.ease_factor,
        interval=db_card.interval,
        repetitions=db_card.repetitions,
        next_review=db_card.next_review,
        options=[CardOptionResponse(id=opt.id, text=opt.text) for opt in options]
    )
    return card_response


@router.get("/{card_id}/study", response_model=CardStudyResponse)
async def get_card_study_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a card in study mode (without correct answer indicators).
    
    Returns question, options (without is_correct), and time thresholds.
    Used for study sessions where user needs to select an answer.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardStudyResponse: Card in study format
        
    Raises:
        HTTPException: If card or deck not found or not owned by user
    """
    db_card = get_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    from app.models.card import CardOption
    options = db.query(CardOption).filter(CardOption.card_id == card_id).order_by(CardOption.order).all()
    
    return CardStudyResponse(
        question=db_card.front,
        options=[CardOptionResponse(id=opt.id, text=opt.text) for opt in options],
        time_thresholds={
            "fast_ms": settings.FAST_RESPONSE_MS,
            "medium_ms": settings.MEDIUM_RESPONSE_MS
        }
    )

@router.put("/{card_id}", response_model=CardResponse)
async def update_card_endpoint(
    deck_id: int,
    card_id: int,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a card.
    
    Updates the front and/or back text of a card.
    Only cards in decks owned by the current user can be updated.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        card_update: Card update data (front, back)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Updated card information
        
    Raises:
        HTTPException: If card not found or not owned by user
    """
    db_card = update_card(
        db=db,
        card_id=card_id,
        card_update=card_update,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return db_card

@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a card.
    
    Permanently deletes a card from a deck.
    Only cards in decks owned by the current user can be deleted.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If card not found or not owned by user
    """
    success = delete_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return None

@router.post("/{card_id}/review", response_model=CardResponse)
async def review_card_endpoint(
    deck_id: int,
    card_id: int,
    review: CardReview,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Review a card and update its scheduling using SM-2 algorithm (legacy endpoint).
    
    Submits a review quality rating (1-5) for a card and updates its
    spaced repetition schedule accordingly.
    
    Note: For MCQ cards, use /submit-answer endpoint instead.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        review: Review data containing quality (1-5)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Updated card with new scheduling information
        
    Raises:
        HTTPException: If card not found, quality invalid, or not owned by user
    """
    if review.quality < 1 or review.quality > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality must be between 1 and 5"
        )
    
    db_card = review_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id,
        quality=review.quality
    )
    
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    return db_card


@router.post("/{card_id}/submit-answer", response_model=AnswerResponse)
async def submit_answer_endpoint(
    deck_id: int,
    card_id: int,
    answer: AnswerSubmission,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer to an MCQ card and get results.
    
    Processes the answer, calculates SM-2 quality automatically from correctness
    and response time, updates card schedule, tracks streaks, and persists the review.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        answer: Answer submission (selected_option_id, response_time_ms)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AnswerResponse: Correctness, correct option, explanation, updated SM-2 values, streaks
        
    Raises:
        HTTPException: If card/option not found or invalid
    """
    result = submit_answer(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id,
        selected_option_id=answer.selected_option_id,
        response_time_ms=answer.response_time_ms
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card or option not found"
        )
    
    return AnswerResponse(**result)

