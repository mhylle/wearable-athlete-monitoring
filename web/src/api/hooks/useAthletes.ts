import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { Athlete, AthleteProfile } from "@/types/api";

export function useAthletes() {
  return useQuery<Athlete[]>({
    queryKey: ["athletes"],
    queryFn: async () => {
      const response = await apiClient.get<Athlete[]>("/api/v1/athletes");
      return response.data;
    },
  });
}

export function useAthlete(id: string) {
  return useQuery<Athlete>({
    queryKey: ["athletes", id],
    queryFn: async () => {
      const response = await apiClient.get<Athlete>(`/api/v1/athletes/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useAthleteProfile(id: string) {
  return useQuery<AthleteProfile>({
    queryKey: ["athletes", id, "profile"],
    queryFn: async () => {
      const response = await apiClient.get<AthleteProfile>(
        `/api/v1/athletes/${id}/profile`
      );
      return response.data;
    },
    enabled: !!id,
  });
}
