import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomeScreen } from '@/features/home/HomeScreen';
import { useAuthStore } from '@/auth/authStore';

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
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

const mockRecovery = {
  total_score: 82,
  hrv_component: 20,
  sleep_component: 25,
  load_component: 18,
  subjective_component: 19,
};

const mockACWR = [
  {
    acute_ewma: 450,
    chronic_ewma: 400,
    acwr_value: 1.12,
    zone: 'optimal',
    date: '2026-02-28',
  },
];

const mockHRV = {
  rolling_mean: 55.3,
  rolling_cv: 0.12,
  trend: 'stable',
  baseline_mean: 52.0,
  history: [
    { date: '2026-02-22', rmssd_value: 50 },
    { date: '2026-02-23', rmssd_value: 53 },
    { date: '2026-02-24', rmssd_value: 48 },
    { date: '2026-02-25', rmssd_value: 56 },
    { date: '2026-02-26', rmssd_value: 58 },
    { date: '2026-02-27', rmssd_value: 55 },
    { date: '2026-02-28', rmssd_value: 57 },
  ],
};

const mockSleep = [
  {
    date: '2026-02-28',
    total_minutes: 465,
    deep_minutes: 90,
    rem_minutes: 110,
    efficiency: 88,
  },
];

const mockAnomalies = [
  {
    athlete_id: 'athlete-1',
    metric_type: 'resting_hr',
    value: 72,
    expected_median: 55,
    mad_score: 3.5,
    severity: 'high',
    anomaly_type: 'spike',
    explanation: 'Resting heart rate unusually elevated',
    detected_at: '2026-02-28T08:00:00Z',
  },
];

describe('HomeScreen (Metrics Dashboard)', () => {
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

    mockGet.mockImplementation((url: string) => {
      if (url.includes('/recovery'))
        return Promise.resolve({ data: mockRecovery });
      if (url.includes('/acwr')) return Promise.resolve({ data: mockACWR });
      if (url.includes('/hrv')) return Promise.resolve({ data: mockHRV });
      if (url.includes('/sleep')) return Promise.resolve({ data: mockSleep });
      if (url.includes('/anomalies'))
        return Promise.resolve({ data: mockAnomalies });
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  it('renders recovery score with value', async () => {
    const { getByTestId } = renderWithProviders(<HomeScreen />);

    await waitFor(() => {
      expect(getByTestId('recovery-score')).toBeTruthy();
    });

    expect(getByTestId('recovery-score').props.children).toBe(82);
  });

  it('renders ACWR zone', async () => {
    const { getByTestId } = renderWithProviders(<HomeScreen />);

    await waitFor(() => {
      expect(getByTestId('acwr-zone')).toBeTruthy();
    });

    expect(getByTestId('acwr-zone').props.children).toBe('Optimal');
  });

  it('renders HRV card with trend', async () => {
    const { getByText } = renderWithProviders(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('55.3 ms')).toBeTruthy();
    });

    expect(getByText('Trend: stable')).toBeTruthy();
  });

  it('renders sleep data', async () => {
    const { getByText } = renderWithProviders(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('7h 45m')).toBeTruthy();
    });

    expect(getByText('88% efficiency')).toBeTruthy();
  });

  it('renders anomalies when present', async () => {
    const { getByTestId, getByText } = renderWithProviders(<HomeScreen />);

    await waitFor(() => {
      expect(getByTestId('anomalies-card')).toBeTruthy();
    });

    expect(
      getByText('Resting heart rate unusually elevated'),
    ).toBeTruthy();
  });

  it('renders greeting with user name', () => {
    const { getByText } = renderWithProviders(<HomeScreen />);
    expect(getByText('Welcome, Test Athlete')).toBeTruthy();
  });
});
