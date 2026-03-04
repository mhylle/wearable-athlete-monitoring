import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WellnessFormScreen } from '@/features/wellness/WellnessFormScreen';
import { useAuthStore } from '@/auth/authStore';

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn(),
}));

const mockPost = jest.fn();
const mockPut = jest.fn();
const mockGet = jest.fn();

jest.mock('@/api/client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
  },
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe('WellnessFormScreen', () => {
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
    // Default: no existing wellness entry (404)
    mockGet.mockRejectedValue({ response: { status: 404 } });
  });

  it('renders all form fields', () => {
    const { getByTestId } = renderWithProviders(<WellnessFormScreen />);

    expect(getByTestId('srpe-slider')).toBeTruthy();
    expect(getByTestId('duration-input')).toBeTruthy();
    expect(getByTestId('soreness-slider')).toBeTruthy();
    expect(getByTestId('fatigue-slider')).toBeTruthy();
    expect(getByTestId('mood-picker')).toBeTruthy();
    expect(getByTestId('sleep-quality-picker')).toBeTruthy();
    expect(getByTestId('notes-input')).toBeTruthy();
    expect(getByTestId('submit-button')).toBeTruthy();
  });

  it('allows selecting sRPE value', () => {
    const { getByTestId } = renderWithProviders(
      <WellnessFormScreen />,
    );

    fireEvent.press(getByTestId('srpe-slider-8'));
    // The active button (8) should exist and be pressable
    expect(getByTestId('srpe-slider-8')).toBeTruthy();
  });

  it('allows entering session duration', () => {
    const { getByTestId } = renderWithProviders(<WellnessFormScreen />);

    fireEvent.changeText(getByTestId('duration-input'), '90');
    expect(getByTestId('duration-input').props.value).toBe('90');
  });

  it('allows selecting mood', () => {
    const { getByTestId } = renderWithProviders(<WellnessFormScreen />);

    fireEvent.press(getByTestId('mood-picker-4'));
    // Mood 4 = "Good" button pressed
    expect(getByTestId('mood-picker-4')).toBeTruthy();
  });

  it('submits wellness entry', async () => {
    mockPost.mockResolvedValue({
      data: {
        id: 'wellness-1',
        athlete_id: 'athlete-1',
        date: '2026-02-28',
        srpe: 5,
        session_duration_minutes: 60,
        soreness: 5,
        fatigue: 5,
        mood: 3,
        sleep_quality: 3,
        notes: null,
      },
    });

    const { getByTestId } = renderWithProviders(<WellnessFormScreen />);

    fireEvent.press(getByTestId('submit-button'));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/v1/wellness', {
        srpe: 5,
        session_duration_minutes: 60,
        soreness: 5,
        fatigue: 5,
        mood: 3,
        sleep_quality: 3,
        notes: undefined,
      });
    });
  });

  it('pre-fills form when today entry exists', async () => {
    const today = new Date().toISOString().slice(0, 10);
    mockGet.mockResolvedValue({
      data: {
        id: 'existing-1',
        athlete_id: 'athlete-1',
        date: today,
        srpe: 7,
        session_duration_minutes: 90,
        soreness: 3,
        fatigue: 6,
        mood: 4,
        sleep_quality: 5,
        notes: 'Felt good',
      },
    });

    const { getByTestId, getByText } = renderWithProviders(
      <WellnessFormScreen />,
    );

    await waitFor(() => {
      expect(getByText('Editing today\'s entry')).toBeTruthy();
    });

    expect(getByTestId('duration-input').props.value).toBe('90');
    expect(getByTestId('notes-input').props.value).toBe('Felt good');
  });
});
