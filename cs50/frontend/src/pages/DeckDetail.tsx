import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Card, Deck } from '../types';
import { format } from 'date-fns';
import './DeckDetail.css';

interface DeckDetailProps {
  onLogout: () => void;
}

export default function DeckDetail({ onLogout }: DeckDetailProps) {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [newCardFront, setNewCardFront] = useState('');
  const [newCardBack, setNewCardBack] = useState('');
  const [showNewCardForm, setShowNewCardForm] = useState(false);
  const [dueCount, setDueCount] = useState(0);
  const loadDataInProgress = useRef(false);

  useEffect(() => {
    if (!deckId) return;
    
    // Prevent duplicate requests (e.g., from React StrictMode)
    if (loadDataInProgress.current) {
      return;
    }

    loadDataInProgress.current = true;
    loadData();
  }, [deckId]);

  const loadData = async () => {
    if (!deckId) return;
    try {
      const [deckData, cardsData, dueData] = await Promise.all([
        apiClient.getDeck(Number(deckId)),
        apiClient.getCards(Number(deckId)),
        apiClient.getDueCardsCount(Number(deckId)),
      ]);
      setDeck(deckData);
      setCards(cardsData);
      setDueCount(dueData.due_count);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      loadDataInProgress.current = false;
    }
  };

  const handleCreateCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deckId) return;
    try {
      const card = await apiClient.createCard(
        Number(deckId),
        newCardFront,
        newCardBack
      );
      setCards([...cards, card]);
      setNewCardFront('');
      setNewCardBack('');
      setShowNewCardForm(false);
      loadData(); // Reload to get updated due count
    } catch (error) {
      console.error('Failed to create card:', error);
    }
  };

  const handleUpdateCard = async (cardId: number, front: string, back: string) => {
    if (!deckId) return;
    try {
      const updatedCard = await apiClient.updateCard(
        Number(deckId),
        cardId,
        front,
        back
      );
      setCards(cards.map((c) => (c.id === cardId ? updatedCard : c)));
      setEditingCard(null);
    } catch (error) {
      console.error('Failed to update card:', error);
    }
  };

  const handleDeleteCard = async (cardId: number) => {
    if (!confirm('Are you sure you want to delete this card?')) return;
    if (!deckId) return;
    try {
      await apiClient.deleteCard(Number(deckId), cardId);
      setCards(cards.filter((c) => c.id !== cardId));
      loadData(); // Reload to get updated due count
    } catch (error) {
      console.error('Failed to delete card:', error);
    }
  };

  const filteredCards = cards.filter(
    (card) =>
      card.front.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.back.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="deck-detail">
      <header className="deck-detail-header">
        <div>
          <button onClick={() => navigate('/')} className="back-btn">
            Back
          </button>
          <h1>
            <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>📚</span>
            {deck?.title}
          </h1>
          {deck?.description && <p>{deck.description}</p>}
        </div>
        <div className="header-actions">
          {dueCount > 0 && (
            <button
              onClick={() => navigate(`/decks/${deckId}/study`)}
              className="btn-primary study-btn"
            >
              Study ({dueCount} due)
            </button>
          )}
        </div>
      </header>

      <div className="deck-detail-content">
        <div className="deck-controls">
          <input
            type="text"
            placeholder="Search cards..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button
            onClick={() => setShowNewCardForm(!showNewCardForm)}
            className="btn-primary"
          >
            {showNewCardForm ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Cancel
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                New Card
              </>
            )}
          </button>
        </div>

        {showNewCardForm && (
          <form onSubmit={handleCreateCard} className="new-card-form">
            <input
              type="text"
              placeholder="Front"
              value={newCardFront}
              onChange={(e) => setNewCardFront(e.target.value)}
              required
            />
            <textarea
              placeholder="Back"
              value={newCardBack}
              onChange={(e) => setNewCardBack(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Create Card
            </button>
          </form>
        )}

        <div className="cards-list">
          {filteredCards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onEdit={setEditingCard}
              onUpdate={handleUpdateCard}
              onDelete={handleDeleteCard}
            />
          ))}
        </div>

        {filteredCards.length === 0 && (
          <div className="empty-state">
            <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📝</div>
            <p>No cards found. Create your first card to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface CardItemProps {
  card: Card;
  onEdit: (card: Card) => void;
  onUpdate: (cardId: number, front: string, back: string) => void;
  onDelete: (cardId: number) => void;
}

function CardItem({ card, onEdit, onUpdate, onDelete }: CardItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [front, setFront] = useState(card.front);
  const [back, setBack] = useState(card.back);

  const handleSave = () => {
    onUpdate(card.id, front, back);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFront(card.front);
    setBack(card.back);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="card-item editing">
        <input
          type="text"
          value={front}
          onChange={(e) => setFront(e.target.value)}
          className="card-input"
        />
        <textarea
          value={back}
          onChange={(e) => setBack(e.target.value)}
          className="card-textarea"
        />
        <div className="card-actions">
          <button onClick={handleSave} className="btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Save
          </button>
          <button onClick={handleCancel} className="btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card-item">
      <div className="card-content">
        <div className="card-front">
          <strong>Front:</strong> {card.front}
        </div>
        <div className="card-back">
          <strong>Back:</strong> {card.back}
        </div>
        <div className="card-stats">
          <span>Ease: {card.ease_factor.toFixed(2)}</span>
          <span>Interval: {card.interval} days</span>
          <span>Reps: {card.repetitions}</span>
          {card.next_review && (
            <span>
              Next: {format(new Date(card.next_review), 'MMM d, yyyy')}
            </span>
          )}
          {!card.next_review && <span className="never-reviewed">Never reviewed</span>}
        </div>
      </div>
      <div className="card-actions">
        <button onClick={() => setIsEditing(true)} className="btn-icon btn-edit" title="Edit">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button onClick={() => onDelete(card.id)} className="btn-icon btn-delete" title="Delete">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
  );
}
