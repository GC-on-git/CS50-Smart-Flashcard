import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { CardStudy, AnswerResponse, Deck, Card } from '../types';
import { useToastContext } from '../contexts/ToastContext';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import './StudySession.css';

interface StudySessionProps {
  onLogout: () => void;
}

export default function StudySession({ onLogout: _onLogout }: StudySessionProps) {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]); // Store full card data
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [currentCard, setCurrentCard] = useState<CardStudy | null>(null);
  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [streaks, setStreaks] = useState({ current_session_streak: 0, daily_streak: 0 });
  const [showCardList, setShowCardList] = useState(false);
  const [visitedCards, setVisitedCards] = useState<Set<number>>(new Set());
  const [attemptedCards, setAttemptedCards] = useState<Set<number>>(new Set());
  const [studyMode, setStudyMode] = useState<'normal' | 'hard'>('normal');
  
  // Session timer (shown to user)
  const [sessionStartTime] = useState<number>(Date.now());
  const [sessionTime, setSessionTime] = useState<number>(0);
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Per-card timer (internal, not shown)
  const [cardStartTime, setCardStartTime] = useState<number | null>(null);
  
  const loadDataInProgress = useRef(false);
  const getDueCardsInProgress = useRef(false);
  const toast = useToastContext();

  useEffect(() => {
    if (!deckId) return;
    
    if (loadDataInProgress.current) {
      return;
    }

    loadDataInProgress.current = true;
    loadData();
  }, [deckId, studyMode]);

  useEffect(() => {
    // Start session timer
    sessionTimerRef.current = setInterval(() => {
      setSessionTime(Date.now() - sessionStartTime);
    }, 100);

    return () => {
      if (sessionTimerRef.current) {
        clearInterval(sessionTimerRef.current);
      }
    };
  }, [sessionStartTime]);

  useEffect(() => {
    // Load current card when index changes
    if (cards.length > 0 && currentCardIndex < cards.length) {
      loadCurrentCard();
    } else if (cards.length > 0 && currentCardIndex >= cards.length) {
      checkForMoreCards();
    }
  }, [currentCardIndex, cards]);

  const handleNext = useCallback(() => {
    setCurrentCardIndex(prev => {
      if (prev < cards.length - 1) {
        return prev + 1;
      }
      // If at the end, increment anyway - useEffect will handle loading more cards
      return prev + 1;
    });
  }, [cards.length]);

  const handlePrev = useCallback(() => {
    setCurrentCardIndex(prev => {
      if (prev > 0) {
        return prev - 1;
      }
      return prev;
    });
  }, []);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onNumberKey: (num) => {
      if (currentCard && !answerResult && num >= 1 && num <= currentCard.options.length) {
        const optionIndex = num - 1;
        const option = currentCard.options[optionIndex];
        if (option) {
          handleOptionSelect(option.id);
        }
      }
    },
    onArrowLeft: handlePrev,
    onArrowRight: () => {
      if (answerResult) {
        handleNext();
      }
    },
    enabled: !loading && !completed && currentCard !== null,
  });

  const loadData = async () => {
    if (!deckId) return;
    try {
      const mode = studyMode === 'hard' ? 'hard' : undefined;
      const [deckData, cardsData] = await Promise.all([
        apiClient.getDeck(Number(deckId)),
        apiClient.getDueCards(Number(deckId), 100, mode),
      ]);
      setDeck(deckData);
      setCards(cardsData);
      if (cardsData.length === 0) {
        setCompleted(true);
      }
    } catch (error: any) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load study session data');
    } finally {
      setLoading(false);
      loadDataInProgress.current = false;
    }
  };

  const loadCurrentCard = async () => {
    if (!deckId || cards.length === 0 || currentCardIndex >= cards.length) return;
    
    try {
      const cardId = cards[currentCardIndex].id;
      const cardData = await apiClient.getCardForStudy(Number(deckId), cardId);
      setCurrentCard(cardData);
      setAnswerResult(null);
      setSelectedOptionId(null);
      
      // Mark card as visited
      setVisitedCards(prev => new Set(prev).add(cardId));
      
      // Start per-card timer (internal, not shown)
      setCardStartTime(Date.now());
    } catch (error: any) {
      console.error('Failed to load card:', error);
      toast.error('Failed to load card');
    }
  };

  const checkForMoreCards = async () => {
    if (!deckId || getDueCardsInProgress.current) return;
    
    getDueCardsInProgress.current = true;
    try {
      const mode = studyMode === 'hard' ? 'hard' : undefined;
      const remainingCards = await apiClient.getDueCards(Number(deckId), 100, mode);
      if (remainingCards.length > 0) {
        setCards(remainingCards);
        setCurrentCardIndex(0);
      } else {
        setCompleted(true);
      }
    } catch (error: any) {
      console.error('Failed to check for more cards:', error);
      toast.error('Failed to load more cards');
    } finally {
      getDueCardsInProgress.current = false;
    }
  };

  const handleOptionSelect = async (optionId: number) => {
    if (!deckId || !currentCard || cardStartTime === null || answerResult !== null) return;

    // Calculate response time (internal, not shown to user)
    const responseTimeMs = Date.now() - cardStartTime;
    setCardStartTime(null);
    setSelectedOptionId(optionId);

    try {
      const cardId = cards[currentCardIndex].id;
      const result = await apiClient.submitAnswer(Number(deckId), cardId, {
        selected_option_id: optionId,
        response_time_ms: responseTimeMs,
      });
      
      setAnswerResult(result);
      setStreaks(result.streaks);
      
      // Mark card as attempted
      setAttemptedCards(prev => new Set(prev).add(cards[currentCardIndex].id));
      
      // Auto-advance after 2 seconds
      setTimeout(() => {
        handleNext();
      }, 2000);
    } catch (error: any) {
      console.error('Failed to submit answer:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit answer');
    }
  };


  const formatTime = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (completed || cards.length === 0) {
    return (
      <div className="study-session">
        <header className="study-header">
          <button onClick={() => navigate(`/decks/${deckId}`)} className="back-btn" title="Back to Deck">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <h1>{deck?.title} - Study Session</h1>
        </header>
        <div className="study-complete">
          <h2>Great job!</h2>
          <p>You've completed all cards due for review.</p>
          <div className="streak-display">
            <p>Session Streak: {streaks.current_session_streak}</p>
            <p>Daily Streak: {streaks.daily_streak}</p>
          </div>
          <div className="session-time-display">
            <p>Session Time: {formatTime(sessionTime)}</p>
          </div>
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

  if (!currentCard) {
    return <div className="loading">Loading card...</div>;
  }

  const progress = ((currentCardIndex + 1) / cards.length) * 100;

  return (
    <div className="study-session">
      <header className="study-header">
        <button onClick={() => navigate(`/decks/${deckId}`)} className="back-btn" title="Back to Deck">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <h1>{deck?.title} - Study Session</h1>
        <div className="header-actions">
          <select
            value={studyMode}
            onChange={(e) => setStudyMode(e.target.value as 'normal' | 'hard')}
            className="study-mode-select"
            title="Study mode"
          >
            <option value="normal">Normal</option>
            <option value="hard">Hard Mode</option>
          </select>
          <button
            onClick={() => setShowCardList(!showCardList)}
            className="btn-icon"
            title="Toggle card list"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="8" y1="6" x2="21" y2="6"></line>
              <line x1="8" y1="12" x2="21" y2="12"></line>
              <line x1="8" y1="18" x2="21" y2="18"></line>
              <line x1="3" y1="6" x2="3.01" y2="6"></line>
              <line x1="3" y1="12" x2="3.01" y2="12"></line>
              <line x1="3" y1="18" x2="3.01" y2="18"></line>
            </svg>
          </button>
        </div>
      </header>

      <div className="study-session-info">
        <div className="streak-display-header">
          <div className="streak-item">
            <span className="streak-label">Session:</span>
            <span className="streak-value">{streaks.current_session_streak}</span>
          </div>
          <div className="streak-item">
            <span className="streak-label">Daily:</span>
            <span className="streak-value">{streaks.daily_streak}</span>
          </div>
        </div>
        <div className="session-timer-container">
          <div className="session-timer">
            <svg className="timer-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span className="timer-text">{formatTime(sessionTime)}</span>
          </div>
        </div>
        <div className="progress-info">
          Card {currentCardIndex + 1} of {cards.length}
        </div>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>

      <div className="study-content-wrapper">
        {showCardList && (
          <div className="card-list-sidebar">
            <div className="card-list-header">
              <h3>Cards</h3>
              <button onClick={() => setShowCardList(false)} className="close-btn">×</button>
            </div>
            <div className="card-list">
              {cards.map((card, idx) => {
                const isVisited = visitedCards.has(card.id);
                const isAttempted = attemptedCards.has(card.id);
                const isCurrent = idx === currentCardIndex;
                
                let statusClass = 'unvisited';
                let statusIcon = '○';
                if (isAttempted) {
                  statusClass = 'attempted';
                  statusIcon = '✓';
                } else if (isVisited) {
                  statusClass = 'visited';
                  statusIcon = '◐';
                }
                
                return (
                  <div
                    key={card.id}
                    className={`card-list-item ${isCurrent ? 'active' : ''} ${statusClass}`}
                    onClick={() => setCurrentCardIndex(idx)}
                  >
                    <div className="card-list-status">{statusIcon}</div>
                    <div className="card-list-number">{idx + 1}</div>
                    <div className="card-list-content">
                      <div className="card-list-question">{card.front}</div>
                      <div className="card-list-stats">
                        <span>Ease: {card.ease_factor.toFixed(2)}</span>
                        <span>Interval: {card.interval}d</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="study-content">
          <div className="card-display">
            <div className="card-question">
              <h2>Question</h2>
              <p>{currentCard.question}</p>
            </div>

            {!answerResult ? (
              <div className="options-container">
                {currentCard.options.map((option) => (
                  <button
                    key={option.id}
                    className="option-button"
                    onClick={() => handleOptionSelect(option.id)}
                    disabled={cardStartTime === null}
                  >
                    {option.text}
                  </button>
                ))}
              </div>
            ) : (
              <div className="answer-result">
                <div className="options-container">
                  {currentCard.options.map((option) => {
                    const isCorrect = option.id === answerResult.correct_option_id;
                    const isSelected = option.id === selectedOptionId;
                    const wasWrong = !answerResult.correct && isSelected;
                    
                    let className = "option-button";
                    if (isCorrect) {
                      className += " correct-option";
                    }
                    if (wasWrong) {
                      className += " wrong-option";
                    }
                    if (isCorrect && !isSelected && !answerResult.correct) {
                      className += " correct-missed";
                    }
                    
                    return (
                      <button
                        key={option.id}
                        className={className}
                        disabled
                      >
                        {option.text}
                      </button>
                    );
                  })}
                </div>
                
                <div className="explanation">
                  <h3>{answerResult.correct ? '✓ Correct!' : '✗ Incorrect'}</h3>
                  <p>{answerResult.explanation}</p>
                </div>
              </div>
            )}

            <div className="card-navigation">
              <button
                onClick={handlePrev}
                disabled={currentCardIndex === 0}
                className="nav-button prev-button"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
                Previous
              </button>
              <button
                onClick={handleNext}
                disabled={currentCardIndex >= cards.length - 1 && answerResult === null}
                className="nav-button next-button"
              >
                Next
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
