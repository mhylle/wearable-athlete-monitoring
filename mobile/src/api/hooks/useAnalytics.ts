import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/auth/authStore';
import type {
  RecoveryScore,
  ACWRResult,
  HRVAnalysis,
  SleepAnalysis,
  AnomaliesResponse,
} from '@/types/api';

function useAthleteId(): string {
  return useAuthStore((s) => s.user?.id ?? '');
}

export function useRecoveryScore() {
  const athleteId = useAthleteId();
  return useQuery<RecoveryScore>({
    queryKey: ['analytics', 'recovery', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<RecoveryScore>(
        `/api/v1/analytics/athlete/${athleteId}/recovery`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useACWR() {
  const athleteId = useAthleteId();
  return useQuery<ACWRResult>({
    queryKey: ['analytics', 'acwr', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<ACWRResult>(
        `/api/v1/analytics/athlete/${athleteId}/acwr`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useHRV() {
  const athleteId = useAthleteId();
  return useQuery<HRVAnalysis>({
    queryKey: ['analytics', 'hrv', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<HRVAnalysis>(
        `/api/v1/analytics/athlete/${athleteId}/hrv`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useSleep() {
  const athleteId = useAthleteId();
  return useQuery<SleepAnalysis>({
    queryKey: ['analytics', 'sleep', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<SleepAnalysis>(
        `/api/v1/analytics/athlete/${athleteId}/sleep`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useAnomalies() {
  const athleteId = useAthleteId();
  return useQuery<AnomaliesResponse>({
    queryKey: ['analytics', 'anomalies', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<AnomaliesResponse>(
        `/api/v1/analytics/athlete/${athleteId}/anomalies`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}
