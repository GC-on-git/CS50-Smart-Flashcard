import axios, { AxiosInstance } from 'axios';
import type { 
  Card, 
  CardReview, 
  Deck, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse,
  User,
  DueCardsCount
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

  logout(): void {
    localStorage.removeItem('access_token');
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

  async createCard(deckId: number, front: string, back: string): Promise<Card> {
    const response = await this.client.post<Card>(`/decks/${deckId}/cards`, { front, back });
    return response.data;
  }

  async updateCard(deckId: number, cardId: number, front: string, back: string): Promise<Card> {
    const response = await this.client.put<Card>(`/decks/${deckId}/cards/${cardId}`, { front, back });
    return response.data;
  }

  async deleteCard(deckId: number, cardId: number): Promise<void> {
    await this.client.delete(`/decks/${deckId}/cards/${cardId}`);
  }

  // Review endpoints
  async reviewCard(deckId: number, cardId: number, quality: number): Promise<Card> {
    const response = await this.client.post<Card>(
      `/decks/${deckId}/cards/${cardId}/review`,
      { quality }
    );
    return response.data;
  }

  async getDueCards(deckId: number, limit: number = 100): Promise<Card[]> {
    const response = await this.client.get<Card[]>(`/decks/${deckId}/cards/due`, {
      params: { limit },
    });
    return response.data;
  }

  async getDueCardsCount(deckId: number): Promise<DueCardsCount> {
    const response = await this.client.get<DueCardsCount>(`/decks/${deckId}/cards/due/count`);
    return response.data;
  }
}

export const apiClient = new ApiClient();
