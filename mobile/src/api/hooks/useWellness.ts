import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/auth/authStore';
import type { WellnessEntry, WellnessSubmission } from '@/types/api';

export function useLatestWellness() {
  const athleteId = useAuthStore((s) => s.user?.id ?? '');
  return useQuery<WellnessEntry | null>({
    queryKey: ['wellness', 'latest', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<WellnessEntry>(
        `/api/v1/wellness/athlete/${athleteId}/latest`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useSubmitWellness() {
  const queryClient = useQueryClient();
  const athleteId = useAuthStore.getState().user?.id ?? '';
  return useMutation<WellnessEntry, Error, WellnessSubmission>({
    mutationFn: async (data) => {
      const response = await apiClient.post<WellnessEntry>(
        '/api/v1/wellness',
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wellness', 'latest', athleteId] });
    },
  });
}

export function useUpdateWellness() {
  const queryClient = useQueryClient();
  const athleteId = useAuthStore.getState().user?.id ?? '';
  return useMutation<
    WellnessEntry,
    Error,
    { id: string; data: Partial<WellnessSubmission> }
  >({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put<WellnessEntry>(
        `/api/v1/wellness/${id}`,
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wellness', 'latest', athleteId] });
    },
  });
}
