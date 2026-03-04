import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionHistoryScreen } from '@/features/sessions/SessionHistoryScreen';
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

const mockSessions = [
  {
    id: 'session-1',
    athlete_id: 'athlete-1',
    source: 'garmin',
    session_type: 'running',
    start_time: '2026-02-28T10:00:00Z',
    duration_minutes: 45,
    hr_avg: 155,
    hr_max: 178,
    distance_meters: 8500,
    calories: 420,
  },
  {
    id: 'session-2',
    athlete_id: 'athlete-1',
    source: 'manual',
    session_type: 'strength',
    start_time: '2026-02-27T15:00:00Z',
    duration_minutes: 60,
    hr_avg: null,
    hr_max: null,
    distance_meters: null,
    calories: null,
  },
];

describe('SessionHistoryScreen', () => {
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
    mockGet.mockResolvedValue({ data: mockSessions });
  });

  it('renders session list', async () => {
    const { getByTestId } = renderWithProviders(<SessionHistoryScreen />);

    await waitFor(() => {
      expect(getByTestId('session-list')).toBeTruthy();
    });
  });

  it('renders sessions with type and source', async () => {
    const { getByTestId } = renderWithProviders(<SessionHistoryScreen />);

    await waitFor(() => {
      expect(getByTestId('session-session-1')).toBeTruthy();
      expect(getByTestId('session-session-2')).toBeTruthy();
    });

    expect(getByTestId('source-session-1').props.children).toBe('garmin');
    expect(getByTestId('source-session-2').props.children).toBe('manual');
  });

  it('shows session details on tap', async () => {
    const { getByTestId, getByText } = renderWithProviders(
      <SessionHistoryScreen />,
    );

    await waitFor(() => {
      expect(getByTestId('session-session-1')).toBeTruthy();
    });

    fireEvent.press(getByTestId('session-session-1'));

    await waitFor(() => {
      expect(getByTestId('details-session-1')).toBeTruthy();
    });

    expect(getByText('Avg HR: 155 bpm')).toBeTruthy();
    expect(getByText('Distance: 8.5 km')).toBeTruthy();
  });

  it('shows empty state when no sessions', async () => {
    mockGet.mockResolvedValue({ data: [] });

    const { getByText } = renderWithProviders(<SessionHistoryScreen />);

    await waitFor(() => {
      expect(getByText('No sessions found')).toBeTruthy();
    });
  });
});
