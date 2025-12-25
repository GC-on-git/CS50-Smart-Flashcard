export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

export interface Deck {
  id: number;
  title: string;
  description?: string;
  owner_id: number;
  created_at: string;
  updated_at?: string;
}

export interface Card {
  id: number;
  deck_id: number;
  front: string;
  back: string;
  created_at: string;
  updated_at?: string;
  ease_factor: number;
  interval: number;
  repetitions: number;
  next_review?: string;
}

export interface CardReview {
  quality: number; // 0-5
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
