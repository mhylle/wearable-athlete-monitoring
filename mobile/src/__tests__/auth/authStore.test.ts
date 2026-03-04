import { useAuthStore } from '@/auth/authStore';

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
}));

// Mock axios
jest.mock('axios', () => {
  const actual = jest.requireActual('axios');
  return {
    ...actual,
    default: {
      ...actual.default,
      post: jest.fn(),
      get: jest.fn(),
    },
    post: jest.fn(),
    get: jest.fn(),
    isAxiosError: jest.fn().mockReturnValue(false),
  };
});

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state between tests
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    });
  });

  it('starts with unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
  });

  it('updates state after successful login', async () => {
    const axios = require('axios');
    const mockUser = {
      id: '1',
      email: 'athlete@test.com',
      role: 'athlete',
      full_name: 'Test Athlete',
      team_id: null,
    };

    axios.post.mockResolvedValueOnce({
      data: {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
      },
    });

    axios.get.mockResolvedValueOnce({ data: mockUser });

    await useAuthStore.getState().login('athlete@test.com', 'password123');

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(state.accessToken).toBe('test-access-token');
    expect(state.refreshToken).toBe('test-refresh-token');
  });

  it('clears state after logout', async () => {
    // Set some state first
    useAuthStore.setState({
      user: {
        id: '1',
        email: 'test@test.com',
        role: 'athlete',
        full_name: 'Test',
        team_id: null,
      },
      accessToken: 'token',
      refreshToken: 'refresh',
      isAuthenticated: true,
      isLoading: false,
    });

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
  });
});
