import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useToastContext } from '../contexts/ToastContext';
import LoadingSkeleton from '../components/LoadingSkeleton';
import './Statistics.css';

interface StatisticsProps {
  onLogout?: () => void;
}

interface StatisticsOverview {
  total_cards: number;
  total_decks: number;
  total_reviews: number;
  mastery_rate: number;
  cards_due: number;
  mastered_cards: number;
}

interface DeckStat {
  deck_id: number;
  deck_title: string;
  total_cards: number;
  mastered_cards: number;
  difficult_cards: number;
  cards_due: number;
  total_reviews: number;
  mastery_rate: number;
  average_ease_factor: number;
}

interface ReviewTimeline {
  date: string;
  count: number;
}

interface DifficultCard {
  card_id: number;
  deck_id: number;
  deck_title: string;
  front: string;
  ease_factor: number;
  interval: number;
  repetitions: number;
  next_review: string | null;
}

export default function Statistics({ onLogout: _onLogout }: StatisticsProps) {
  const navigate = useNavigate();
  const toast = useToastContext();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<StatisticsOverview | null>(null);
  const [deckStats, setDeckStats] = useState<DeckStat[]>([]);
  const [reviewsTimeline, setReviewsTimeline] = useState<ReviewTimeline[]>([]);
  const [difficultCards, setDifficultCards] = useState<DifficultCard[]>([]);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const [overviewData, decksData, timelineData, difficultData] = await Promise.all([
        apiClient.getStatisticsOverview(),
        apiClient.getDecksStatistics(),
        apiClient.getReviewsTimeline(30),
        apiClient.getDifficultCards(20),
      ]);
      setOverview(overviewData);
      setDeckStats(decksData);
      setReviewsTimeline(timelineData);
      setDifficultCards(difficultData);
    } catch (error: any) {
      console.error('Failed to load statistics:', error);
      toast.error(error.response?.data?.detail || 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="statistics-page">
        <div className="statistics-header">
          <LoadingSkeleton width="200px" height="40px" />
        </div>
        <div className="statistics-grid">
          {[...Array(4)].map((_, i) => (
            <LoadingSkeleton key={i} width="100%" height="150px" borderRadius="12px" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="statistics-page">
      <header className="statistics-header">
        <button onClick={() => navigate('/')} className="back-btn" title="Back to Dashboard">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <h1>Statistics & Progress</h1>
      </header>

      <div className="statistics-content">
        {overview && (
          <section className="statistics-section">
            <h2>Overview</h2>
            <div className="statistics-grid">
              <div className="stat-card">
                <div className="stat-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                    <polyline points="2 17 12 22 22 17"></polyline>
                    <polyline points="2 12 12 17 22 12"></polyline>
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-label">Total Cards</div>
                  <div className="stat-value">{overview.total_cards}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-label">Total Decks</div>
                  <div className="stat-value">{overview.total_decks}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-label">Total Reviews</div>
                  <div className="stat-value">{overview.total_reviews}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-label">Mastery Rate</div>
                  <div className="stat-value">{overview.mastery_rate.toFixed(1)}%</div>
                  <div className="stat-subtext">
                    {overview.mastered_cards} of {overview.total_cards} cards
                  </div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-label">Cards Due</div>
                  <div className="stat-value">{overview.cards_due}</div>
                </div>
              </div>
            </div>
          </section>
        )}

        {deckStats.length > 0 && (
          <section className="statistics-section">
            <h2>Deck Statistics</h2>
            <div className="deck-stats-table">
              <table>
                <thead>
                  <tr>
                    <th>Deck</th>
                    <th>Total Cards</th>
                    <th>Mastered</th>
                    <th>Difficult</th>
                    <th>Due</th>
                    <th>Mastery Rate</th>
                    <th>Avg Ease</th>
                  </tr>
                </thead>
                <tbody>
                  {deckStats.map((deck) => (
                    <tr
                      key={deck.deck_id}
                      onClick={() => navigate(`/decks/${deck.deck_id}`)}
                      className="deck-stat-row"
                    >
                      <td>{deck.deck_title}</td>
                      <td>{deck.total_cards}</td>
                      <td>{deck.mastered_cards}</td>
                      <td>{deck.difficult_cards}</td>
                      <td>{deck.cards_due}</td>
                      <td>{deck.mastery_rate.toFixed(1)}%</td>
                      <td>{deck.average_ease_factor.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {reviewsTimeline.length > 0 && (
          <section className="statistics-section">
            <h2>Review Activity (Last 30 Days)</h2>
            <div className="timeline-chart">
              <div className="timeline-bars">
                {reviewsTimeline.map((item, index) => {
                  const maxCount = Math.max(...reviewsTimeline.map(i => i.count), 1);
                  const width = (item.count / maxCount) * 100;
                  return (
                    <div key={index} className="timeline-bar-container">
                      <div className="timeline-label">
                        {new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </div>
                      <div className="timeline-bar-wrapper">
                        <div
                          className="timeline-bar"
                          style={{ width: `${width}%` }}
                          title={`${item.date}: ${item.count} reviews`}
                        />
                        <div className="timeline-value">{item.count}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {difficultCards.length > 0 && (
          <section className="statistics-section">
            <h2>Difficult Cards</h2>
            <div className="difficult-cards-list">
              {difficultCards.map((card) => (
                <div
                  key={card.card_id}
                  className="difficult-card-item"
                  onClick={() => navigate(`/decks/${card.deck_id}`)}
                >
                  <div className="difficult-card-header">
                    <span className="difficult-card-deck">{card.deck_title}</span>
                    <span className="difficult-card-ease">Ease: {card.ease_factor.toFixed(2)}</span>
                  </div>
                  <div className="difficult-card-front">{card.front}</div>
                  <div className="difficult-card-stats">
                    <span>Interval: {card.interval}d</span>
                    <span>Reps: {card.repetitions}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {!loading && deckStats.length === 0 && (
          <div className="empty-state">
            <div style={{ marginBottom: '1rem', opacity: 0.5, display: 'flex', justifyContent: 'center' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
              </svg>
            </div>
            <p>No statistics available. Start studying to see your progress!</p>
          </div>
        )}
      </div>
    </div>
  );
}

