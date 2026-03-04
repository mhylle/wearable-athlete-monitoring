import React from 'react';
import { render } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppNavigator } from '@/navigation/AppNavigator';
import { useAuthStore } from '@/auth/authStore';

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
}));

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(),
  get: jest.fn(),
  isAxiosError: jest.fn().mockReturnValue(false),
  create: jest.fn(() => ({
    get: jest.fn().mockRejectedValue(new Error('not mocked')),
    post: jest.fn(),
    put: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}));

jest.mock('react-native-svg', () => {
  const { View } = require('react-native');
  return {
    __esModule: true,
    default: View,
    Svg: View,
    Polyline: View,
  };
});

// Mock Health Connect service
jest.mock('@/features/health-connect/healthConnectService', () => ({
  isHealthConnectAvailable: jest.fn(() => false),
  requestPermissions: jest.fn().mockResolvedValue(false),
  readHealthData: jest.fn().mockResolvedValue({
    metrics: [],
    exercise_sessions: [],
    changes_token: null,
  }),
}));

describe('AppNavigator', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: {
        id: '1',
        email: 'athlete@test.com',
        role: 'athlete',
        full_name: 'Test Athlete',
        team_id: null,
      },
      accessToken: 'token',
      refreshToken: 'refresh',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
  });

  it('renders tab navigation when authenticated', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { getAllByText } = render(
      <QueryClientProvider client={queryClient}>
        <NavigationContainer>
          <AppNavigator />
        </NavigationContainer>
      </QueryClientProvider>,
    );

    // Tab labels appear in both the header and tab bar, so use getAllByText
    expect(getAllByText('Home').length).toBeGreaterThanOrEqual(1);
    expect(getAllByText('Wellness').length).toBeGreaterThanOrEqual(1);
    expect(getAllByText('Sessions').length).toBeGreaterThanOrEqual(1);
    expect(getAllByText('Health').length).toBeGreaterThanOrEqual(1);
    expect(getAllByText('Profile').length).toBeGreaterThanOrEqual(1);
  });
});
