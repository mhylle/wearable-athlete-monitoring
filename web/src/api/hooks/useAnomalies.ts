import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { Anomaly } from "@/types/api";

export function useAthleteAnomalies(id: string) {
  return useQuery<Anomaly[]>({
    queryKey: ["anomalies", id],
    queryFn: async () => {
      const response = await apiClient.get<{ athlete_id: string; anomalies: Anomaly[]; date: string }>(
        `/api/v1/analytics/athlete/${id}/anomalies`
      );
      return response.data.anomalies;
    },
    enabled: !!id,
  });
}

export function useTeamAnomalies() {
  return useQuery<Anomaly[]>({
    queryKey: ["anomalies", "team"],
    queryFn: async () => {
      const response = await apiClient.get<{ anomalies: Anomaly[]; date: string }>(
        "/api/v1/analytics/team/anomalies"
      );
      return response.data.anomalies;
    },
  });
}
