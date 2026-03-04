import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { Platform } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HealthConnectScreen } from '@/features/health-connect/HealthConnectScreen';
import { useAuthStore } from '@/auth/authStore';

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
}));

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock('@/api/client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}));

// Mock the health connect service module
jest.mock('@/features/health-connect/healthConnectService', () => ({
  isHealthConnectAvailable: jest.fn(() => false),
  requestPermissions: jest.fn().mockResolvedValue(false),
  readHealthData: jest.fn().mockResolvedValue({
    metrics: [],
    exercise_sessions: [],
    changes_token: null,
  }),
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe('HealthConnectScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Platform.OS = 'android';
    useAuthStore.setState({
      user: {
        id: 'athlete-1',
        email: 'athlete@test.com',
        role: 'athlete',
        full_name: 'Test Athlete',
        team_id: 'team-1',
      },
      accessToken: 'token',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
  });

  it('shows not connected status initially', async () => {
    mockGet.mockResolvedValue({
      data: { connected: false, last_sync_at: null },
    });

    const { getByTestId } = renderWithProviders(<HealthConnectScreen />);

    await waitFor(() => {
      expect(getByTestId('hc-connection-status').props.children).toBe(
        'Not Connected',
      );
    });
  });

  it('shows connected status when synced', async () => {
    mockGet.mockResolvedValue({
      data: { connected: true, last_sync_at: '2026-03-02T10:00:00Z' },
    });

    const { getByTestId } = renderWithProviders(<HealthConnectScreen />);

    await waitFor(() => {
      expect(getByTestId('hc-connection-status').props.children).toBe(
        'Connected',
      );
    });
  });

  it('shows sync button when connected', async () => {
    mockGet.mockResolvedValue({
      data: { connected: true, last_sync_at: '2026-03-02T10:00:00Z' },
    });

    const { getByTestId } = renderWithProviders(<HealthConnectScreen />);

    await waitFor(() => {
      expect(getByTestId('hc-sync-button')).toBeTruthy();
    });
  });

  it('shows iOS message on non-android platform', async () => {
    Platform.OS = 'ios';
    mockGet.mockResolvedValue({
      data: { connected: false, last_sync_at: null },
    });

    const { getByText } = renderWithProviders(<HealthConnectScreen />);

    await waitFor(() => {
      expect(
        getByText(/Health Connect is only available on Android/),
      ).toBeTruthy();
    });
  });
});
