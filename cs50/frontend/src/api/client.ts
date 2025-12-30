import axios, { AxiosInstance } from 'axios';
import type { 
  Card, 
  CardStudy,
  AnswerSubmission,
  AnswerResponse,
  Deck, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse,
  User,
  DueCardsCount,
  UserPreferences,
  UserPreferencesUpdate
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token refresh on 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', data);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', data);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  }

  async getProfile(): Promise<User> {
    const response = await this.client.get<User>('/auth/profile');
    return response.data;
  }

  async getStreaks(): Promise<{ current_session_streak: number; daily_streak: number }> {
    const response = await this.client.get<{ current_session_streak: number; daily_streak: number }>('/users/streaks');
    return response.data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
  }

  // Preferences endpoints
  async getUserPreferences(): Promise<UserPreferences> {
    const response = await this.client.get<UserPreferences>('/preferences');
    return response.data;
  }

  async updateUserPreferences(preferences: UserPreferencesUpdate): Promise<UserPreferences> {
    const response = await this.client.put<UserPreferences>('/preferences', preferences);
    return response.data;
  }

  // Legacy aliases for backward compatibility
  async getPreferences(): Promise<UserPreferences> {
    return this.getUserPreferences();
  }

  async updatePreferences(preferences: UserPreferencesUpdate): Promise<UserPreferences> {
    return this.updateUserPreferences(preferences);
  }

  // Deck endpoints
  async getDecks(query?: string): Promise<Deck[]> {
    const response = await this.client.get<Deck[]>('/decks', {
      params: { query },
    });
    return response.data;
  }

  async getDeck(deckId: number): Promise<Deck> {
    const response = await this.client.get<Deck>(`/decks/${deckId}`);
    return response.data;
  }

  async createDeck(title: string, description?: string): Promise<Deck> {
    const response = await this.client.post<Deck>('/decks', { title, description });
    return response.data;
  }

  async updateDeck(deckId: number, title: string, description?: string): Promise<Deck> {
    const response = await this.client.put<Deck>(`/decks/${deckId}`, { title, description });
    return response.data;
  }

  async deleteDeck(deckId: number): Promise<void> {
    await this.client.delete(`/decks/${deckId}`);
  }

  // Card endpoints
  async getCards(deckId: number, query?: string): Promise<Card[]> {
    const response = await this.client.get<Card[]>(`/decks/${deckId}/cards`, {
      params: { query },
    });
    return response.data;
  }

  async getCard(deckId: number, cardId: number): Promise<Card> {
    const response = await this.client.get<Card>(`/decks/${deckId}/cards/${cardId}`);
    return response.data;
  }

  async getCardForStudy(deckId: number, cardId: number): Promise<CardStudy> {
    const response = await this.client.get<CardStudy>(`/decks/${deckId}/cards/${cardId}/study`);
    return response.data;
  }

  async createCard(deckId: number, front: string, explanation: string, options: Array<{text: string, is_correct: boolean}>): Promise<Card> {
    const response = await this.client.post<Card>(`/decks/${deckId}/cards`, { 
      front, 
      explanation,
      options 
    });
    return response.data;
  }

  async generateCards(deckId: number, topic: string, numCards: number): Promise<Card[]> {
    const response = await this.client.post<Card[]>(`/decks/${deckId}/cards/generate`, {
      topic,
      num_cards: numCards,
    });
    return response.data;
  }

  async updateCard(deckId: number, cardId: number, front: string, explanation: string): Promise<Card> {
    const response = await this.client.put<Card>(`/decks/${deckId}/cards/${cardId}`, { front, explanation });
    return response.data;
  }

  async deleteCard(deckId: number, cardId: number): Promise<void> {
    await this.client.delete(`/decks/${deckId}/cards/${cardId}`);
  }

  async bulkDeleteCards(deckId: number, cardIds: number[]): Promise<void> {
    await this.client.post(`/decks/${deckId}/cards/bulk-delete`, { card_ids: cardIds });
  }

  async duplicateCard(deckId: number, cardId: number): Promise<Card> {
    const response = await this.client.post<Card>(`/decks/${deckId}/cards/${cardId}/duplicate`);
    return response.data;
  }

  // Review endpoints
  async reviewCard(deckId: number, cardId: number, quality: number): Promise<Card> {
    const response = await this.client.post<Card>(
      `/decks/${deckId}/cards/${cardId}/review`,
      { quality }
    );
    return response.data;
  }

  async submitAnswer(deckId: number, cardId: number, answer: AnswerSubmission): Promise<AnswerResponse> {
    const response = await this.client.post<AnswerResponse>(
      `/decks/${deckId}/cards/${cardId}/submit-answer`,
      answer
    );
    return response.data;
  }

  async getDueCards(deckId: number, limit: number = 100, mode?: string): Promise<Card[]> {
    const response = await this.client.get<Card[]>(`/decks/${deckId}/cards/due`, {
      params: { limit, ...(mode && { mode }) },
    });
    return response.data;
  }

  async getDueCardsCount(deckId: number): Promise<DueCardsCount> {
    const response = await this.client.get<DueCardsCount>(`/decks/${deckId}/cards/due/count`);
    return response.data;
  }

  // Statistics endpoints
  async getStatisticsOverview(): Promise<any> {
    const response = await this.client.get('/statistics/overview');
    return response.data;
  }

  async getDecksStatistics(): Promise<any[]> {
    const response = await this.client.get('/statistics/decks');
    return response.data;
  }

  async getDeckStatistics(deckId: number): Promise<any> {
    const response = await this.client.get(`/statistics/decks/${deckId}`);
    return response.data;
  }

  async getReviewsTimeline(days: number = 30): Promise<any[]> {
    const response = await this.client.get('/statistics/reviews-timeline', {
      params: { days },
    });
    return response.data;
  }

  async getDifficultCards(limit: number = 20): Promise<any[]> {
    const response = await this.client.get('/statistics/difficult-cards', {
      params: { limit },
    });
    return response.data;
  }

}

export const apiClient = new ApiClient();
