import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { WellnessEntry, TeamWellnessStatus } from "@/types/api";

export interface WellnessParams {
  start_date?: string;
  end_date?: string;
}

export function useAthleteWellness(id: string, params?: WellnessParams) {
  return useQuery<WellnessEntry[]>({
    queryKey: ["wellness", id, params],
    queryFn: async () => {
      const response = await apiClient.get<{ entries: WellnessEntry[]; count: number }>(
        `/api/v1/wellness/athlete/${id}`,
        { params }
      );
      return response.data.entries;
    },
    enabled: !!id,
  });
}

export function useTeamWellnessOverview() {
  return useQuery<TeamWellnessStatus[]>({
    queryKey: ["wellness", "team", "overview"],
    queryFn: async () => {
      const response = await apiClient.get<TeamWellnessStatus[]>(
        "/api/v1/wellness/team/overview"
      );
      return response.data;
    },
  });
}
