import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Linking } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GarminConnectScreen } from '@/features/garmin/GarminConnectScreen';
import { useAuthStore } from '@/auth/authStore';

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
}));

const mockGet = jest.fn();

jest.mock('@/api/client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

jest.spyOn(Linking, 'openURL').mockResolvedValue(true);

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

describe('GarminConnectScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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

  it('shows connect button when disconnected', async () => {
    mockGet.mockResolvedValue({
      data: {
        id: 'profile-1',
        user_id: 'athlete-1',
        position: null,
        height_cm: null,
        weight_kg: null,
        garmin_connected: false,
        last_sync_at: null,
      },
    });

    const { getByTestId } = renderWithProviders(<GarminConnectScreen />);

    await waitFor(() => {
      expect(getByTestId('garmin-connect-button')).toBeTruthy();
    });

    expect(getByTestId('garmin-connection-status').props.children).toBe(
      'Not Connected',
    );
  });

  it('shows connected status when linked', async () => {
    mockGet.mockResolvedValue({
      data: {
        id: 'profile-1',
        user_id: 'athlete-1',
        position: null,
        height_cm: null,
        weight_kg: null,
        garmin_connected: true,
        last_sync_at: '2026-02-28T10:00:00Z',
      },
    });

    const { getByTestId, queryByTestId } = renderWithProviders(
      <GarminConnectScreen />,
    );

    await waitFor(() => {
      expect(getByTestId('garmin-connection-status').props.children).toBe(
        'Connected',
      );
    });

    expect(queryByTestId('garmin-connect-button')).toBeNull();
  });

  it('opens OAuth URL when connect button pressed', async () => {
    mockGet.mockResolvedValue({
      data: {
        id: 'profile-1',
        user_id: 'athlete-1',
        position: null,
        height_cm: null,
        weight_kg: null,
        garmin_connected: false,
        last_sync_at: null,
      },
    });

    const { getByTestId } = renderWithProviders(<GarminConnectScreen />);

    await waitFor(() => {
      expect(getByTestId('garmin-connect-button')).toBeTruthy();
    });

    fireEvent.press(getByTestId('garmin-connect-button'));

    await waitFor(() => {
      expect(Linking.openURL).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/garmin/oauth/start'),
      );
    });
  });
});
