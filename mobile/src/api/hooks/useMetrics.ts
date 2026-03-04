import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/auth/authStore';

function useAthleteId(): string {
  return useAuthStore((s) => s.user?.id ?? '');
}

export interface DailyMetricDataPoint {
  date: string;
  avg: number;
  min: number;
  max: number;
  count: number;
}

export interface DailyMetricsResponse {
  metric_type: string;
  start: string;
  end: string;
  data: DailyMetricDataPoint[];
}

export interface AvailableMetricsResponse {
  athlete_id: string;
  metric_types: string[];
}

export function useAvailableMetrics() {
  const athleteId = useAthleteId();
  return useQuery<AvailableMetricsResponse>({
    queryKey: ['metrics', 'available', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<AvailableMetricsResponse>(
        `/api/v1/metrics/athlete/${athleteId}/available`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useMetricSeries(metricType: string, days: number = 30) {
  const athleteId = useAthleteId();
  const end = new Date().toISOString().split('T')[0];
  const start = new Date(Date.now() - days * 86400000).toISOString().split('T')[0];

  return useQuery<DailyMetricsResponse>({
    queryKey: ['metrics', 'daily', athleteId, metricType, days],
    queryFn: async () => {
      const response = await apiClient.get<DailyMetricsResponse>(
        `/api/v1/metrics/athlete/${athleteId}/daily`,
        { params: { metric_type: metricType, start, end } },
      );
      return response.data;
    },
    enabled: !!athleteId && !!metricType,
  });
}
