import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/auth/authStore';
import type { Session } from '@/types/api';

export function useSessions() {
  const athleteId = useAuthStore((s) => s.user?.id ?? '');
  return useQuery<Session[]>({
    queryKey: ['sessions', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<Session[]>(
        `/api/v1/sessions/athlete/${athleteId}`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}
