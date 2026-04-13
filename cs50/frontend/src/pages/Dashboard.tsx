import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Deck, User } from '../types';
import Modal from '../components/Modal';
import { useToastContext } from '../contexts/ToastContext';
import { DeckCardSkeleton } from '../components/LoadingSkeleton';
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
  const [dailyStreak, setDailyStreak] = useState<number>(0);
  const [deckToDelete, setDeckToDelete] = useState<number | null>(null);
  const navigate = useNavigate();
  const loadDataInProgress = useRef(false);
  const toast = useToastContext();

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
      const [decksData, userData, streaksData] = await Promise.all([
        apiClient.getDecks(),
        apiClient.getProfile(),
        apiClient.getStreaks().catch(() => ({ current_session_streak: 0, daily_streak: 0 })),
      ]);
      setDecks(decksData);
      setUser(userData);
      setDailyStreak(streaksData.daily_streak);
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
      toast.success('Deck created successfully!');
    } catch (error: any) {
      console.error('Failed to create deck:', error);
      toast.error(error.response?.data?.detail || 'Failed to create deck');
    }
  };

  const handleDeleteDeckClick = (deckId: number) => {
    setDeckToDelete(deckId);
  };

  const handleDeleteDeckConfirm = async () => {
    if (deckToDelete === null) return;
    try {
      await apiClient.deleteDeck(deckToDelete);
      setDecks(decks.filter((d) => d.id !== deckToDelete));
      toast.success('Deck deleted successfully');
      setDeckToDelete(null);
    } catch (error: any) {
      console.error('Failed to delete deck:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete deck');
      setDeckToDelete(null);
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

  const getDeckToDelete = () => {
    if (deckToDelete === null) return null;
    return decks.find(d => d.id === deckToDelete);
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="decks-grid">
          {[...Array(6)].map((_, i) => (
            <DeckCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <Modal
        isOpen={deckToDelete !== null}
        onClose={() => setDeckToDelete(null)}
        title="Delete Deck"
        onConfirm={handleDeleteDeckConfirm}
        onCancel={() => setDeckToDelete(null)}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonClassName="btn-danger"
      >
        <p>Are you sure you want to delete the deck "{getDeckToDelete()?.title}"?</p>
        <p style={{ color: 'rgba(163, 147, 191, 0.7)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
          This action cannot be undone and will delete all cards in this deck.
        </p>
      </Modal>
      <header className="dashboard-header">
        <div className="header-left">
          <div>
            <h1>Smart Flashcard</h1>
            <p>
              <span style={{ marginRight: '0.5rem', display: 'inline-flex', alignItems: 'center' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </span>
              Welcome, {user?.username}!
            </p>
          </div>
        </div>
        <div className="header-right">
          <div className="header-icons">
            <div className="daily-streak-icon" title={`Daily Streak: ${dailyStreak}`}>
              <span className="streak-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
                </svg>
              </span>
              <span className="streak-count">{dailyStreak}</span>
            </div>
            <button onClick={() => navigate('/statistics')} className="settings-icon-btn" title="Statistics">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
            </button>
            <button onClick={() => navigate('/settings')} className="settings-icon-btn" title="Settings">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            </button>
            <button onClick={handleLogout} className="logout-icon-btn" title="Logout">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        </div>
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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
              onDelete={() => handleDeleteDeckClick(deck.id)}
            />
          ))}
        </div>

        {filteredDecks.length === 0 && (
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
          {deck.title}
        </h3>
        <button onClick={onDelete} className="btn-icon btn-delete" title="Delete deck">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
      {deck.description && <p className="deck-description">{deck.description}</p>}
        <div className="deck-card-footer">
          {dueCount !== null && dueCount > 0 && (
            <span className="due-badge">
              <span style={{ fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', marginRight: '0.25rem' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </span>
              {dueCount} due
            </span>
          )}
          <div className="deck-actions">
            <button onClick={onSelect} className="btn-icon-only" title="View Cards">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
              </svg>
            </button>
            {dueCount !== null && dueCount > 0 && (
              <button
                onClick={() => window.location.href = `/decks/${deck.id}/study`}
                className="btn-icon-only btn-study"
                title="Study"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
              </button>
            )}
          </div>
        </div>
    </div>
  );
}
