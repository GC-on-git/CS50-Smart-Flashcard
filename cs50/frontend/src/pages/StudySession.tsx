import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Card, Deck } from '../types';
import './StudySession.css';

interface StudySessionProps {
  onLogout: () => void;
}

export default function StudySession({ onLogout }: StudySessionProps) {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const loadDataInProgress = useRef(false);
  const getDueCardsInProgress = useRef(false);

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
      const [deckData, cardsData] = await Promise.all([
        apiClient.getDeck(Number(deckId)),
        apiClient.getDueCards(Number(deckId), 100),
      ]);
      setDeck(deckData);
      setCards(cardsData);
      if (cardsData.length === 0) {
        setCompleted(true);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      loadDataInProgress.current = false;
    }
  };

  const handleReview = async (quality: number) => {
    if (!deckId || cards.length === 0) return;

    const currentCard = cards[currentIndex];
    try {
      // Submit review
      await apiClient.reviewCard(Number(deckId), currentCard.id, quality);

      // Move to next card or finish
      if (currentIndex < cards.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setShowAnswer(false);
      } else {
        // Reload due cards to see if there are more
        // Prevent duplicate requests
        if (getDueCardsInProgress.current) {
          return;
        }

        getDueCardsInProgress.current = true;
        try {
          const remainingCards = await apiClient.getDueCards(Number(deckId), 100);
          if (remainingCards.length > 0) {
            setCards(remainingCards);
            setCurrentIndex(0);
            setShowAnswer(false);
          } else {
            setCompleted(true);
          }
        } finally {
          getDueCardsInProgress.current = false;
        }
      }
    } catch (error) {
      console.error('Failed to submit review:', error);
      getDueCardsInProgress.current = false;
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (completed || cards.length === 0) {
    return (
      <div className="study-session">
        <header className="study-header">
          <button onClick={() => navigate(`/decks/${deckId}`)} className="back-btn">
            ← Back to Deck
          </button>
          <h1>{deck?.title} - Study Session</h1>
        </header>
        <div className="study-complete">
          <h2>Great job!</h2>
          <p>You've completed all cards due for review.</p>
          <button
            onClick={() => navigate(`/decks/${deckId}`)}
            className="btn-primary"
          >
            Back to Deck
          </button>
        </div>
      </div>
    );
  }

  const currentCard = cards[currentIndex];
  const progress = ((currentIndex + 1) / cards.length) * 100;

  return (
    <div className="study-session">
      <header className="study-header">
        <button onClick={() => navigate(`/decks/${deckId}`)} className="back-btn">
          ← Back to Deck
        </button>
        <h1>{deck?.title} - Study Session</h1>
        <div className="progress-info">
          Card {currentIndex + 1} of {cards.length}
        </div>
      </header>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>

      <div className="study-content">
        <div className="card-display">
          <div className="card-front-display">
            <h2>Question</h2>
            <p>{currentCard.front}</p>
          </div>

          {showAnswer ? (
            <div className="card-back-display">
              <h2>Answer</h2>
              <p>{currentCard.back}</p>
              <div className="quality-buttons">
                <p className="quality-prompt">How well did you remember this?</p>
                <div className="quality-grid">
                  <QualityButton
                    quality={0}
                    label="Blackout"
                    emoji=""
                    onClick={() => handleReview(0)}
                  />
                  <QualityButton
                    quality={1}
                    label="Incorrect"
                    emoji=""
                    onClick={() => handleReview(1)}
                  />
                  <QualityButton
                    quality={2}
                    label="Hard"
                    emoji=""
                    onClick={() => handleReview(2)}
                  />
                  <QualityButton
                    quality={3}
                    label="Good"
                    emoji=""
                    onClick={() => handleReview(3)}
                  />
                  <QualityButton
                    quality={4}
                    label="Easy"
                    emoji=""
                    onClick={() => handleReview(4)}
                  />
                  <QualityButton
                    quality={5}
                    label="Perfect"
                    emoji=""
                    onClick={() => handleReview(5)}
                  />
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAnswer(true)}
              className="show-answer-btn"
            >
              Show Answer
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface QualityButtonProps {
  quality: number;
  label: string;
  emoji: string;
  onClick: () => void;
}

function QualityButton({ quality, label, emoji, onClick }: QualityButtonProps) {
  const getColor = (q: number) => {
    if (q < 3) return '#f44336';
    if (q === 3) return '#ff9800';
    if (q === 4) return '#4caf50';
    return '#2196f3';
  };

  return (
    <button
      className="quality-btn"
      onClick={onClick}
      style={{ borderColor: getColor(quality) }}
    >
      <span className="quality-emoji">{emoji}</span>
      <span className="quality-label">{label}</span>
      <span className="quality-number">{quality}</span>
    </button>
  );
}
