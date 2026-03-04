import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/auth/authStore';
import type { AthleteProfile } from '@/types/api';

export function useProfile() {
  const athleteId = useAuthStore((s) => s.user?.id ?? '');
  return useQuery<AthleteProfile>({
    queryKey: ['profile', athleteId],
    queryFn: async () => {
      const response = await apiClient.get<AthleteProfile>(
        `/api/v1/athletes/${athleteId}/profile`,
      );
      return response.data;
    },
    enabled: !!athleteId,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const athleteId = useAuthStore.getState().user?.id ?? '';
  return useMutation<
    AthleteProfile,
    Error,
    Partial<Pick<AthleteProfile, 'position' | 'height_cm' | 'weight_kg'>>
  >({
    mutationFn: async (data) => {
      const response = await apiClient.put<AthleteProfile>(
        `/api/v1/athletes/${athleteId}/profile`,
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', athleteId] });
    },
  });
}
