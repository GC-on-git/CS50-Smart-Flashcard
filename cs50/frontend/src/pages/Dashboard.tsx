import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Deck, User } from '../types';
import './Dashboard.css';

interface DashboardProps {
  onLogout: () => void;
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [newDeckTitle, setNewDeckTitle] = useState('');
  const [newDeckDescription, setNewDeckDescription] = useState('');
  const [showNewDeckForm, setShowNewDeckForm] = useState(false);
  const navigate = useNavigate();
  const loadDataInProgress = useRef(false);

  useEffect(() => {
    // Prevent duplicate requests (e.g., from React StrictMode)
    if (loadDataInProgress.current) {
      return;
    }

    loadDataInProgress.current = true;
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [decksData, userData] = await Promise.all([
        apiClient.getDecks(),
        apiClient.getProfile(),
      ]);
      setDecks(decksData);
      setUser(userData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      loadDataInProgress.current = false;
    }
  };

  const handleCreateDeck = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const deck = await apiClient.createDeck(newDeckTitle, newDeckDescription);
      setDecks([...decks, deck]);
      setNewDeckTitle('');
      setNewDeckDescription('');
      setShowNewDeckForm(false);
    } catch (error) {
      console.error('Failed to create deck:', error);
    }
  };

  const handleDeleteDeck = async (deckId: number) => {
    if (!confirm('Are you sure you want to delete this deck?')) return;
    try {
      await apiClient.deleteDeck(deckId);
      setDecks(decks.filter((d) => d.id !== deckId));
    } catch (error) {
      console.error('Failed to delete deck:', error);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    onLogout();
  };

  const filteredDecks = decks.filter(
    (deck) =>
      deck.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      deck.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>
            <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>📚</span>
            Smart Flashcard
          </h1>
          <p>
            <span style={{ marginRight: '0.5rem' }}>👋</span>
            Welcome, {user?.username}!
          </p>
        </div>
        <button onClick={handleLogout} className="logout-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          Logout
        </button>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-controls">
          <div className="search-input-wrapper">
            <input
              type="text"
              placeholder="Search decks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          <button
            onClick={() => setShowNewDeckForm(!showNewDeckForm)}
            className="btn-primary"
          >
            {showNewDeckForm ? (
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
                New Deck
              </>
            )}
          </button>
        </div>

        {showNewDeckForm && (
          <form onSubmit={handleCreateDeck} className="new-deck-form">
            <input
              type="text"
              placeholder="Deck title"
              value={newDeckTitle}
              onChange={(e) => setNewDeckTitle(e.target.value)}
              required
            />
            <textarea
              placeholder="Description (optional)"
              value={newDeckDescription}
              onChange={(e) => setNewDeckDescription(e.target.value)}
            />
            <button type="submit" className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                <polyline points="17 21 17 13 7 13 7 21"></polyline>
                <polyline points="7 3 7 8 15 8"></polyline>
              </svg>
              Create Deck
            </button>
          </form>
        )}

        <div className="decks-grid">
          {filteredDecks.map((deck) => (
            <DeckCard
              key={deck.id}
              deck={deck}
              onSelect={() => navigate(`/decks/${deck.id}`)}
              onDelete={() => handleDeleteDeck(deck.id)}
            />
          ))}
        </div>

        {filteredDecks.length === 0 && (
          <div className="empty-state">
            <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📝</div>
            <p>No decks found. Create your first deck to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface DeckCardProps {
  deck: Deck;
  onSelect: () => void;
  onDelete: () => void;
}

function DeckCard({ deck, onSelect, onDelete }: DeckCardProps) {
  const [dueCount, setDueCount] = useState<number | null>(null);
  const requestInProgress = useRef(false);

  useEffect(() => {
    // Prevent duplicate requests (e.g., from React StrictMode)
    if (requestInProgress.current) {
      return;
    }

    requestInProgress.current = true;

    const loadDueCount = async () => {
      try {
        const data = await apiClient.getDueCardsCount(deck.id);
        setDueCount(data.due_count);
      } catch (error) {
        console.error('Failed to load due count:', error);
      } finally {
        requestInProgress.current = false;
      }
    };

    loadDueCount();
  }, [deck.id]);

  return (
    <div className="deck-card">
      <div className="deck-card-header">
        <h3 onClick={onSelect} className="deck-title">
          <span style={{ fontSize: '1.2rem', marginRight: '0.5rem' }}>📖</span>
          {deck.title}
        </h3>
        <button onClick={onDelete} className="btn-icon btn-delete" title="Delete deck">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
      {deck.description && <p className="deck-description">{deck.description}</p>}
      <div className="deck-card-footer">
        {dueCount !== null && dueCount > 0 && (
          <span className="due-badge">
            <span style={{ fontSize: '0.9rem' }}>⏰</span>
            {dueCount} due
          </span>
        )}
        <div className="deck-actions">
          <button onClick={onSelect} className="btn-secondary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
            View Cards
          </button>
          {dueCount !== null && dueCount > 0 && (
            <button
              onClick={() => window.location.href = `/decks/${deck.id}/study`}
              className="btn-primary"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
              Study
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
