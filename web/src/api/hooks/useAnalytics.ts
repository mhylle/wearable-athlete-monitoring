import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type {
  ACWRResult,
  HRVAnalysis,
  SleepSummary,
  RecoveryScore,
  TeamACWROverview,
  TeamRecoveryOverview,
} from "@/types/api";

export function useAthleteACWR(id: string) {
  // API returns a single ACWRResult object, not an array.
  // We wrap it in an array for the component which expects ACWRResult[].
  return useQuery<ACWRResult[]>({
    queryKey: ["analytics", "acwr", id],
    queryFn: async () => {
      const response = await apiClient.get<ACWRResult>(
        `/api/v1/analytics/athlete/${id}/acwr`
      );
      return [response.data];
    },
    enabled: !!id,
  });
}

export function useAthleteHRV(id: string) {
  // API returns {athlete_id, start, end, daily_values, stats: {rolling_mean, rolling_cv, trend, baseline_mean}}
  // Component expects flat HRVAnalysis with rolling_mean, trend, daily_values at top level.
  return useQuery<HRVAnalysis>({
    queryKey: ["analytics", "hrv", id],
    queryFn: async () => {
      interface RawHRV {
        athlete_id: string;
        start: string;
        end: string;
        daily_values: { date: string; rmssd: number }[];
        stats: { rolling_mean: number; rolling_cv: number; trend: string; baseline_mean: number };
      }
      const response = await apiClient.get<RawHRV>(
        `/api/v1/analytics/athlete/${id}/hrv`
      );
      const raw = response.data;
      return {
        daily_values: raw.daily_values.map((d) => ({ date: d.date, rmssd: d.rmssd })),
        rolling_mean: raw.stats.rolling_mean,
        rolling_cv: raw.stats.rolling_cv,
        trend: raw.stats.trend as HRVAnalysis["trend"],
        baseline_mean: raw.stats.baseline_mean,
      };
    },
    enabled: !!id,
  });
}

export function useAthleteSleep(id: string) {
  // API returns {athlete_id, start, end, daily_summaries: [...], average: {...}}
  return useQuery<SleepSummary[]>({
    queryKey: ["analytics", "sleep", id],
    queryFn: async () => {
      const response = await apiClient.get<{ daily_summaries: SleepSummary[] }>(
        `/api/v1/analytics/athlete/${id}/sleep`
      );
      return response.data.daily_summaries ?? [];
    },
    enabled: !!id,
  });
}

export function useAthleteRecovery(id: string) {
  return useQuery<RecoveryScore>({
    queryKey: ["analytics", "recovery", id],
    queryFn: async () => {
      const response = await apiClient.get<RecoveryScore>(
        `/api/v1/analytics/athlete/${id}/recovery`
      );
      return response.data;
    },
    enabled: !!id,
  });
}

export function useTeamACWROverview() {
  return useQuery<TeamACWROverview[]>({
    queryKey: ["analytics", "team", "acwr-overview"],
    queryFn: async () => {
      interface RawACWRItem {
        athlete_id: string;
        full_name: string;
        acwr: { acwr_value: number; zone: string };
      }
      const response = await apiClient.get<{ athletes: RawACWRItem[]; date: string }>(
        "/api/v1/analytics/team/acwr-overview"
      );
      return response.data.athletes.map((a) => ({
        athlete_id: a.athlete_id,
        athlete_name: a.full_name,
        acwr_value: a.acwr.acwr_value,
        zone: a.acwr.zone as TeamACWROverview["zone"],
      }));
    },
  });
}

// ---------- Metrics endpoints ----------

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

export function useAthleteAvailableMetrics(id: string) {
  return useQuery<AvailableMetricsResponse>({
    queryKey: ["metrics", "available", id],
    queryFn: async () => {
      const response = await apiClient.get<AvailableMetricsResponse>(
        `/api/v1/metrics/athlete/${id}/available`
      );
      return response.data;
    },
    enabled: !!id,
  });
}

export function useAthleteMetricSeries(id: string, metricType: string, days: number = 30) {
  const end = new Date().toISOString().split("T")[0];
  const start = new Date(Date.now() - days * 86400000).toISOString().split("T")[0];

  return useQuery<DailyMetricsResponse>({
    queryKey: ["metrics", "daily", id, metricType, days],
    queryFn: async () => {
      const response = await apiClient.get<DailyMetricsResponse>(
        `/api/v1/metrics/athlete/${id}/daily`,
        { params: { metric_type: metricType, start, end } }
      );
      return response.data;
    },
    enabled: !!id && !!metricType,
  });
}

export function useTeamRecoveryOverview() {
  return useQuery<TeamRecoveryOverview[]>({
    queryKey: ["analytics", "team", "recovery-overview"],
    queryFn: async () => {
      interface RawRecoveryItem {
        athlete_id: string;
        full_name: string;
        recovery_score: { total_score: number };
      }
      const response = await apiClient.get<{ athletes: RawRecoveryItem[]; date: string }>(
        "/api/v1/analytics/team/recovery-overview"
      );
      return response.data.athletes.map((a) => ({
        athlete_id: a.athlete_id,
        athlete_name: a.full_name,
        total_score: a.recovery_score.total_score,
      }));
    },
  });
}
