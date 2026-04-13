import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Card, Deck } from '../types';
import { format } from 'date-fns';
import Modal from '../components/Modal';
import { useToastContext } from '../contexts/ToastContext';
import { CardItemSkeleton } from '../components/LoadingSkeleton';
import './DeckDetail.css';

interface DeckDetailProps {
  onLogout: () => void;
}

export default function DeckDetail({ onLogout: _onLogout }: DeckDetailProps) {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [_editingCard, setEditingCard] = useState<Card | null>(null);
  const [newCardQuestion, setNewCardQuestion] = useState('');
  const [newCardOptions, setNewCardOptions] = useState(['', '', '', '']);
  const [newCardCorrectOption, setNewCardCorrectOption] = useState<number>(0);
  const [newCardExplanation, setNewCardExplanation] = useState('');
  const [showNewCardForm, setShowNewCardForm] = useState(false);
  const [showAIGenerateForm, setShowAIGenerateForm] = useState(false);
  const [aiTopic, setAiTopic] = useState('');
  const [numCards, setNumCards] = useState(10);
  const [isGenerating, setIsGenerating] = useState(false);
  const [dueCount, setDueCount] = useState(0);
  const [cardToDelete, setCardToDelete] = useState<number | null>(null);
  const [selectedCards, setSelectedCards] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<'created' | 'ease' | 'due'>('created');
  const [filterStatus, setFilterStatus] = useState<'all' | 'new' | 'due' | 'mastered' | 'difficult'>('all');
  const loadDataInProgress = useRef(false);
  const toast = useToastContext();

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
    
    // Validate that all options are filled
    if (newCardOptions.some(opt => !opt.trim())) {
      toast.error('Please fill in all 4 options');
      return;
    }
    
    // Validate that question is filled
    if (!newCardQuestion.trim()) {
      toast.error('Please enter a question');
      return;
    }
    
    try {
      const options = newCardOptions.map((text, index) => ({
        text: text.trim(),
        is_correct: index === newCardCorrectOption
      }));
      
      const card = await apiClient.createCard(
        Number(deckId),
        newCardQuestion.trim(),
        newCardExplanation.trim(),
        options
      );
      setCards([...cards, card]);
      setNewCardQuestion('');
      setNewCardOptions(['', '', '', '']);
      setNewCardCorrectOption(0);
      setNewCardExplanation('');
      setShowNewCardForm(false);
      loadData(); // Reload to get updated due count
      toast.success('Card created successfully!');
    } catch (error: any) {
      console.error('Failed to create card:', error);
      toast.error(error.response?.data?.detail || 'Failed to create card. Please try again.');
    }
  };

  const handleGenerateCards = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deckId) return;
    setIsGenerating(true);
    try {
      // Use topic if provided, otherwise pass empty string (backend will use deck context)
      const topic = aiTopic.trim() || '';
      const generatedCards = await apiClient.generateCards(
        Number(deckId),
        topic,
        numCards
      );
      setCards([...generatedCards, ...cards]);
      setAiTopic('');
      setNumCards(10);
      setShowAIGenerateForm(false);
      loadData(); // Reload to get updated due count
      toast.success(`Successfully generated ${generatedCards.length} cards!`);
    } catch (error: any) {
      console.error('Failed to generate cards:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to generate cards. Please check your AI API key is configured.';
      toast.error(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUpdateCard = async (cardId: number, front: string, explanation: string) => {
    if (!deckId) return;
    try {
      const updatedCard = await apiClient.updateCard(
        Number(deckId),
        cardId,
        front,
        explanation || ''
      );
      setCards(cards.map((c) => (c.id === cardId ? updatedCard : c)));
      setEditingCard(null);
      toast.success('Card updated successfully!');
    } catch (error: any) {
      console.error('Failed to update card:', error);
      toast.error(error.response?.data?.detail || 'Failed to update card');
    }
  };

  const handleDeleteCardClick = (cardId: number) => {
    setCardToDelete(cardId);
  };

  const handleDeleteCardConfirm = async () => {
    if (cardToDelete === null || !deckId) return;
    try {
      await apiClient.deleteCard(Number(deckId), cardToDelete);
      setCards(cards.filter((c) => c.id !== cardToDelete));
      loadData(); // Reload to get updated due count
      toast.success('Card deleted successfully');
      setCardToDelete(null);
    } catch (error: any) {
      console.error('Failed to delete card:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete card');
      setCardToDelete(null);
    }
  };

  const getCardToDelete = () => {
    if (cardToDelete === null) return null;
    return cards.find(c => c.id === cardToDelete);
  };

  const filteredCards = cards
    .filter(
      (card) =>
        card.front.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (card.explanation && card.explanation.toLowerCase().includes(searchQuery.toLowerCase()))
    )
    .filter((card) => {
      if (filterStatus === 'all') return true;
      if (filterStatus === 'new') return !card.next_review;
      if (filterStatus === 'due') {
        return card.next_review ? new Date(card.next_review) <= new Date() : true;
      }
      if (filterStatus === 'mastered') return card.ease_factor >= 2.5;
      if (filterStatus === 'difficult') return card.ease_factor < 2.0;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'created') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      if (sortBy === 'ease') {
        return a.ease_factor - b.ease_factor;
      }
      if (sortBy === 'due') {
        if (!a.next_review && !b.next_review) return 0;
        if (!a.next_review) return -1;
        if (!b.next_review) return 1;
        return new Date(a.next_review).getTime() - new Date(b.next_review).getTime();
      }
      return 0;
    });

  if (loading) {
    return (
      <div className="deck-detail">
        <div className="cards-list">
          {[...Array(5)].map((_, i) => (
            <CardItemSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="deck-detail">
      <Modal
        isOpen={cardToDelete !== null}
        onClose={() => setCardToDelete(null)}
        title="Delete Card"
        onConfirm={handleDeleteCardConfirm}
        onCancel={() => setCardToDelete(null)}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonClassName="btn-danger"
      >
        <p>Are you sure you want to delete this card?</p>
        {getCardToDelete() && (
          <p style={{ color: 'rgba(163, 147, 191, 0.7)', fontSize: '0.875rem', marginTop: '0.5rem', fontStyle: 'italic' }}>
            "{getCardToDelete()!.front.substring(0, 50)}{getCardToDelete()!.front.length > 50 ? '...' : ''}"
          </p>
        )}
      </Modal>
      <header className="deck-detail-header">
        <button onClick={() => navigate('/')} className="back-btn" title="Back to Dashboard">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <div className="header-title-container">
          <h1>{deck?.title}</h1>
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
          <div className="sort-filter-menu">
            <select
              value={`${sortBy}-${filterStatus}`}
              onChange={(e) => {
                const [newSort, newFilter] = e.target.value.split('-');
                setSortBy(newSort as 'created' | 'ease' | 'due');
                setFilterStatus(newFilter as 'all' | 'new' | 'due' | 'mastered' | 'difficult');
              }}
              className="sort-filter-select"
              title="Sort & Filter cards"
            >
              <optgroup label="Sort by Created">
                <option value="created-all">All Cards</option>
                <option value="created-new">New</option>
                <option value="created-due">Due</option>
                <option value="created-mastered">Mastered</option>
                <option value="created-difficult">Difficult</option>
              </optgroup>
              <optgroup label="Sort by Ease">
                <option value="ease-all">All Cards</option>
                <option value="ease-new">New</option>
                <option value="ease-due">Due</option>
                <option value="ease-mastered">Mastered</option>
                <option value="ease-difficult">Difficult</option>
              </optgroup>
              <optgroup label="Sort by Due Date">
                <option value="due-all">All Cards</option>
                <option value="due-new">New</option>
                <option value="due-due">Due</option>
                <option value="due-mastered">Mastered</option>
                <option value="due-difficult">Difficult</option>
              </optgroup>
            </select>
          </div>
          {selectedCards.size > 0 && (
            <div className="bulk-actions">
              <span>{selectedCards.size} selected</span>
              <button
                onClick={async () => {
                  if (!deckId) return;
                  try {
                    await apiClient.bulkDeleteCards(Number(deckId), Array.from(selectedCards));
                    setCards(cards.filter(c => !selectedCards.has(c.id)));
                    setSelectedCards(new Set());
                    loadData();
                    toast.success(`Deleted ${selectedCards.size} card(s)`);
                  } catch (error: any) {
                    toast.error(error.response?.data?.detail || 'Failed to delete cards');
                  }
                }}
                className="btn-secondary"
              >
                Delete Selected
              </button>
            </div>
          )}
          <button
            onClick={() => {
              setShowAIGenerateForm(!showAIGenerateForm);
              setShowNewCardForm(false);
            }}
            className="btn-primary"
          >
            {showAIGenerateForm ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Cancel AI
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2v20M2 12h20"></path>
                  <circle cx="12" cy="12" r="10"></circle>
                </svg>
                Generate with AI
              </>
            )}
          </button>
          <button
            onClick={() => {
              setShowNewCardForm(!showNewCardForm);
              setShowAIGenerateForm(false);
            }}
            className="btn-primary"
          >
            {showNewCardForm ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Cancel
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                New Card
              </>
            )}
          </button>
        </div>

        {showAIGenerateForm && (
          <form onSubmit={handleGenerateCards} className="new-card-form ai-generate-form">
            {cards.length > 0 && (
              <div style={{ 
                marginBottom: '1rem', 
                padding: '0.75rem', 
                background: 'rgba(14, 177, 210, 0.1)', 
                borderRadius: '6px',
                border: '1px solid rgba(14, 177, 210, 0.2)'
              }}>
                <div style={{ fontSize: '0.875rem', color: 'rgba(14, 177, 210, 0.9)', marginBottom: '0.5rem', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  Using deck context:
                </div>
                <div style={{ fontSize: '0.875rem', color: 'rgba(224, 224, 224, 0.8)' }}>
                  <div><strong>Title:</strong> {deck?.title}</div>
                  {deck?.description && <div style={{ marginTop: '0.25rem' }}><strong>Description:</strong> {deck.description}</div>}
                </div>
              </div>
            )}
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="ai-topic" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Additional Topic (Optional)
                {cards.length > 0 && (
                  <span style={{ fontSize: '0.75rem', fontWeight: '400', color: 'rgba(163, 147, 191, 0.7)', marginLeft: '0.5rem' }}>
                    - Leave empty to use deck title/description
                  </span>
                )}
              </label>
              <input
                id="ai-topic"
                type="text"
                placeholder={cards.length > 0 ? "e.g., Advanced concepts, Specific subtopics..." : "e.g., Python programming basics, World War II, Photosynthesis..."}
                value={aiTopic}
                onChange={(e) => setAiTopic(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', fontSize: '1rem' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label htmlFor="num-cards" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Number of Cards: {numCards}
              </label>
              <input
                id="num-cards"
                type="range"
                min="1"
                max="50"
                value={numCards}
                onChange={(e) => setNumCards(Number(e.target.value))}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
                <span>1</span>
                <span>50</span>
              </div>
            </div>
            <button 
              type="submit" 
              className="btn-primary" 
              disabled={isGenerating}
              style={{ opacity: isGenerating ? 0.6 : 1 }}
            >
              {isGenerating ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2v20M2 12h20"></path>
                    <circle cx="12" cy="12" r="10"></circle>
                  </svg>
                  Generate {numCards} Cards
                </>
              )}
            </button>
          </form>
        )}

        {showNewCardForm && (
          <form onSubmit={handleCreateCard} className="new-card-form">
            <div className="form-field">
              <label>Question</label>
              <input
                type="text"
                placeholder="Enter the question..."
                value={newCardQuestion}
                onChange={(e) => setNewCardQuestion(e.target.value)}
                required
              />
            </div>
            
            <div className="form-field">
              <label>Options</label>
              {newCardOptions.map((option, index) => (
                <div key={index} className="option-input-wrapper">
                  <input
                    type="radio"
                    name="correct-option"
                    checked={newCardCorrectOption === index}
                    onChange={() => setNewCardCorrectOption(index)}
                    className="correct-option-radio"
                    title="Mark as correct answer"
                  />
                  <input
                    type="text"
                    placeholder={`Option ${index + 1}`}
                    value={option}
                    onChange={(e) => {
                      const newOptions = [...newCardOptions];
                      newOptions[index] = e.target.value;
                      setNewCardOptions(newOptions);
                    }}
                    required
                    className="option-input"
                  />
                </div>
              ))}
            </div>
            
            <div className="form-field">
              <label>Explanation</label>
              <textarea
                placeholder="Enter explanation for the correct answer..."
                value={newCardExplanation}
                onChange={(e) => setNewCardExplanation(e.target.value)}
                className="explanation-textarea"
              />
            </div>
            
            <button type="submit" className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
              onDelete={handleDeleteCardClick}
              onDuplicate={async () => {
                if (!deckId) return;
                try {
                  const duplicated = await apiClient.duplicateCard(Number(deckId), card.id);
                  setCards([duplicated, ...cards]);
                  loadData();
                  toast.success('Card duplicated successfully');
                } catch (error: any) {
                  toast.error(error.response?.data?.detail || 'Failed to duplicate card');
                }
              }}
              isSelected={selectedCards.has(card.id)}
              onSelectToggle={(cardId) => {
                setSelectedCards(prev => {
                  const newSet = new Set(prev);
                  if (newSet.has(cardId)) {
                    newSet.delete(cardId);
                  } else {
                    newSet.add(cardId);
                  }
                  return newSet;
                });
              }}
            />
          ))}
        </div>

        {filteredCards.length === 0 && (
          <div className="empty-state">
            <div style={{ marginBottom: '1rem', opacity: 0.5, display: 'flex', justifyContent: 'center' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
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
  onUpdate: (cardId: number, front: string, explanation: string) => void;
  onDelete: (cardId: number) => void;
  isSelected?: boolean;
  onSelectToggle?: (cardId: number) => void;
  onDuplicate?: () => void;
}

function CardItem({ card, onEdit: _onEdit, onUpdate, onDelete, isSelected = false, onSelectToggle, onDuplicate }: CardItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [front, setFront] = useState(card.front);
  const [explanation, setExplanation] = useState(card.explanation || '');

  const handleSave = () => {
    onUpdate(card.id, front, explanation);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFront(card.front);
    setExplanation(card.explanation || '');
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
          placeholder="Question"
        />
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          className="card-textarea"
          placeholder="Explanation"
        />
        <div className="card-actions">
          <button onClick={handleSave} className="btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Save
          </button>
          <button onClick={handleCancel} className="btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
    <div className={`card-item ${isSelected ? 'selected' : ''}`}>
      {onSelectToggle && (
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelectToggle(card.id)}
          className="card-checkbox"
        />
      )}
      <div className="card-content">
        <div className="card-front">
          <strong>Question:</strong> {card.front}
        </div>
        {card.explanation && (
          <div className="card-explanation">
            <strong>Explanation:</strong> {card.explanation}
          </div>
        )}
        {card.options && card.options.length > 0 && (
          <div className="card-options">
            <strong>Options:</strong>
            <ul>
              {card.options.map((opt) => (
                <li key={opt.id}>{opt.text}</li>
              ))}
            </ul>
          </div>
        )}
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
        {onDuplicate && (
          <button onClick={onDuplicate} className="btn-icon btn-duplicate" title="Duplicate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        )}
        <button onClick={() => setIsEditing(true)} className="btn-icon btn-edit" title="Edit">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button onClick={() => onDelete(card.id)} className="btn-icon btn-delete" title="Delete">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
  );
}
