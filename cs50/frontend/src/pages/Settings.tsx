import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useToastContext } from '../contexts/ToastContext';
import { apiClient } from '../api/client';
import './Settings.css';

interface SettingsProps {
  onLogout: () => void;
}

export default function Settings({ onLogout: _onLogout }: SettingsProps) {
  const navigate = useNavigate();
  const { theme, fontSize, setTheme, setFontSize } = useTheme();
  const toast = useToastContext();
  const [loading, setLoading] = useState(false);
  const [studyPreferences, setStudyPreferences] = useState({
    cards_per_session: 20,
    auto_advance_delay_ms: 2000,
  });

  useEffect(() => {
    // Load current study preferences if available
    const loadPreferences = async () => {
      try {
        const prefs = await apiClient.getUserPreferences();
        if (prefs.study_session_preferences) {
          setStudyPreferences({
            cards_per_session: prefs.study_session_preferences.cards_per_session || 20,
            auto_advance_delay_ms: prefs.study_session_preferences.auto_advance_delay_ms || 2000,
          });
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
      }
    };
    loadPreferences();
  }, []);

  const handleSaveStudyPreferences = async () => {
    setLoading(true);
    try {
      await apiClient.updateUserPreferences({
        study_session_preferences: studyPreferences,
      });
      toast.success('Study preferences saved successfully!');
    } catch (error: any) {
      console.error('Failed to save preferences:', error);
      toast.error(error.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings">
      <header className="settings-header">
        <button onClick={() => navigate('/')} className="back-btn" title="Back to Dashboard">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <h1>Settings</h1>
      </header>

      <div className="settings-content">
        <section className="settings-section">
          <h2>Appearance</h2>
          <div className="settings-group">
            <label htmlFor="theme-select">Theme</label>
            <select
              id="theme-select"
              value={theme}
              onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'auto')}
              className="settings-select"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
            <p className="settings-description">
              Choose your preferred color theme. "Auto" follows your system preference.
            </p>
          </div>

          <div className="settings-group">
            <label htmlFor="font-size-select">Font Size</label>
            <select
              id="font-size-select"
              value={fontSize}
              onChange={(e) => setFontSize(e.target.value as 'small' | 'medium' | 'large')}
              className="settings-select"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
            <p className="settings-description">
              Adjust the font size for better readability.
            </p>
          </div>
        </section>

        <section className="settings-section">
          <h2>Study Session</h2>
          <div className="settings-group">
            <label htmlFor="cards-per-session">Cards per Session</label>
            <input
              id="cards-per-session"
              type="number"
              min="1"
              max="200"
              value={studyPreferences.cards_per_session}
              onChange={(e) =>
                setStudyPreferences({
                  ...studyPreferences,
                  cards_per_session: parseInt(e.target.value) || 20,
                })
              }
              className="settings-input"
            />
            <p className="settings-description">
              Maximum number of cards to review in a single study session.
            </p>
          </div>

          <div className="settings-group">
            <label htmlFor="auto-advance-delay">Auto-advance Delay (ms)</label>
            <input
              id="auto-advance-delay"
              type="number"
              min="0"
              max="10000"
              step="100"
              value={studyPreferences.auto_advance_delay_ms}
              onChange={(e) =>
                setStudyPreferences({
                  ...studyPreferences,
                  auto_advance_delay_ms: parseInt(e.target.value) || 2000,
                })
              }
              className="settings-input"
            />
            <p className="settings-description">
              Delay in milliseconds before automatically advancing to the next card after answering.
            </p>
          </div>

          <button
            onClick={handleSaveStudyPreferences}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Saving...' : 'Save Study Preferences'}
          </button>
        </section>
      </div>
    </div>
  );
}
