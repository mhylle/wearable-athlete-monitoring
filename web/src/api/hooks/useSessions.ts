import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { Session, CreateSessionPayload } from "@/types/api";

export interface SessionFilters {
  session_type?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
}

export function useAthleteSessions(id: string, filters?: SessionFilters) {
  return useQuery<Session[]>({
    queryKey: ["sessions", id, filters],
    queryFn: async () => {
      const response = await apiClient.get<{ sessions: Session[]; count: number }>(
        `/api/v1/sessions/athlete/${id}`,
        { params: filters }
      );
      return response.data.sessions;
    },
    enabled: !!id,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation<Session, Error, CreateSessionPayload>({
    mutationFn: async (payload) => {
      const response = await apiClient.post<Session>(
        "/api/v1/sessions",
        payload
      );
      return response.data;
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["sessions", variables.athlete_id],
      });
    },
  });
}
