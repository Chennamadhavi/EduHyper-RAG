import apiClient from './api';
import { AuthResponse, LoginPayload, RegisterPayload, User } from '../types/auth';

const TOKEN_KEY = 'eduhyperrag_token';
const USER_KEY = 'eduhyperrag_user';

export const authService = {
  /**
   * Sends user credentials to FastAPI backend to obtain a JWT bearer token.
   */
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', payload);
    const data = response.data;
    this.setSession(data.access_token, data.user);
    return data;
  },

  /**
   * Registers a new student or teacher account.
   */
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/auth/register', payload);
    const data = response.data;
    this.setSession(data.access_token, data.user);
    return data;
  },

  /**
   * Fetches the current authenticated user profile using the stored JWT token.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me');
    const user = response.data;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  },

  /**
   * Saves JWT token and user info into local storage and configures Axios headers.
   */
  setSession(token: string | null, user: User | null): void {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem(TOKEN_KEY);
      delete apiClient.defaults.headers.common['Authorization'];
    }

    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  },

  /**
   * Retrieves the stored JWT token.
   */
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Retrieves the cached user info.
   */
  getCachedUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  },

  /**
   * Clears authenticated session state.
   */
  logout(): void {
    this.setSession(null, null);
  },
};

export default authService;
