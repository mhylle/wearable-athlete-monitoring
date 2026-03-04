import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import { API_URL } from '@/utils/constants';
import type { User, TokenResponse } from '@/types/api';

const ACCESS_TOKEN_KEY = 'auth_access_token';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<boolean>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post<TokenResponse>(
        `${API_URL}/api/v1/auth/login`,
        { email, password },
      );
      const { access_token, refresh_token } = response.data;

      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);

      const userResponse = await axios.get<User>(
        `${API_URL}/api/v1/auth/me`,
        { headers: { Authorization: `Bearer ${access_token}` } },
      );

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Login failed. Please check your credentials.';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  refreshAuth: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;

    try {
      const response = await axios.post<TokenResponse>(
        `${API_URL}/api/v1/auth/refresh`,
        { refresh_token: refreshToken },
      );
      const { access_token, refresh_token } = response.data;

      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);

      const userResponse = await axios.get<User>(
        `${API_URL}/api/v1/auth/me`,
        { headers: { Authorization: `Bearer ${access_token}` } },
      );

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        user: userResponse.data,
        isAuthenticated: true,
      });
      return true;
    } catch {
      await get().logout();
      return false;
    }
  },

  initialize: async () => {
    set({ isLoading: true });
    try {
      const accessToken = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);

      if (!accessToken || !refreshToken) {
        set({ isLoading: false });
        return;
      }

      set({ accessToken, refreshToken });

      // Try to fetch user with existing token
      try {
        const userResponse = await axios.get<User>(
          `${API_URL}/api/v1/auth/me`,
          { headers: { Authorization: `Bearer ${accessToken}` } },
        );
        set({
          user: userResponse.data,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch {
        // Token expired, try refresh
        const success = await get().refreshAuth();
        if (!success) {
          set({ isLoading: false });
        } else {
          set({ isLoading: false });
        }
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));
