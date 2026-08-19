import api from './api';
import { AuthResponse, User, UserRole } from '../types';

export const authService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const data = await api.post<AuthResponse>('/auth/login', { email, password });
    if (data.access_token) {
      localStorage.setItem('reliefchain_token', data.access_token);
      localStorage.setItem('reliefchain_user', JSON.stringify(data.user));
    }
    return data;
  },

  async register(payload: {
    email: string;
    password: string;
    full_name: string;
    role: UserRole;
    phone_number?: string;
    skills?: string[];
  }): Promise<AuthResponse> {
    const data = await api.post<AuthResponse>('/auth/register', payload);
    if (data.access_token) {
      localStorage.setItem('reliefchain_token', data.access_token);
      localStorage.setItem('reliefchain_user', JSON.stringify(data.user));
    }
    return data;
  },

  logout(): void {
    localStorage.removeItem('reliefchain_token');
    localStorage.removeItem('reliefchain_user');
  },

  getCurrentUser(): User | null {
    const stored = localStorage.getItem('reliefchain_user');
    return stored ? JSON.parse(stored) : null;
  },

  getToken(): string | null {
    return localStorage.getItem('reliefchain_token');
  },
};
