export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
  streaks?: {
    current_session_streak: number;
    daily_streak: number;
  };
}

export interface Deck {
  id: number;
  title: string;
  description?: string;
  owner_id: number;
  created_at: string;
  updated_at?: string;
}

export interface CardOption {
  id: number;
  text: string;
}

export interface Card {
  id: number;
  deck_id: number;
  front: string;
  explanation?: string;
  created_at: string;
  updated_at?: string;
  ease_factor: number;
  interval: number;
  repetitions: number;
  next_review?: string;
  options?: CardOption[];
}

export interface CardStudy {
  question: string;
  options: CardOption[];
  time_thresholds: {
    fast_ms: number;
    medium_ms: number;
  };
}

export interface AnswerSubmission {
  selected_option_id: number;
  response_time_ms: number;
}

export interface AnswerResponse {
  correct: boolean;
  correct_option_id: number;
  explanation: string;
  updated_card: {
    ease_factor: number;
    interval: number;
    repetitions: number;
    next_review?: string;
  };
  streaks: {
    current_session_streak: number;
    daily_streak: number;
  };
}

export interface Streaks {
  current_session_streak: number;
  daily_streak: number;
}

export interface CardReview {
  quality: number; // 1-5 (legacy)
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface DueCardsCount {
  deck_id: number;
  due_count: number;
}

export interface UserPreferences {
  user_id: number;
  theme: string;
  font_size: string;
  study_session_preferences?: {
    cards_per_session?: number;
    auto_advance_delay_ms?: number;
  };
  created_at: string;
  updated_at?: string;
}

export interface UserPreferencesUpdate {
  theme?: string;
  font_size?: string;
  study_session_preferences?: {
    cards_per_session?: number;
    auto_advance_delay_ms?: number;
  };
}
