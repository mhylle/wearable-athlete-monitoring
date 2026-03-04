/**
 * Hook for syncing Health Connect data to the backend.
 *
 * Reads health data from Health Connect and POSTs it to
 * POST /api/v1/health-data/sync.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import {
  isHealthConnectAvailable,
  readHealthData,
  requestPermissions,
  type HCSyncPayload,
} from './healthConnectService';

interface SyncResponse {
  metrics_synced: number;
  metrics_skipped: number;
  sessions_synced: number;
  sessions_skipped: number;
  errors: string[];
}

interface SyncStatus {
  connected: boolean;
  last_sync_at: string | null;
}

export function useHealthSyncStatus() {
  return useQuery<SyncStatus>({
    queryKey: ['health-connect-status'],
    queryFn: async () => {
      const response = await apiClient.get<SyncStatus>(
        '/api/v1/health-data/status',
      );
      return response.data;
    },
  });
}

export function useHealthDataSync() {
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error, { days?: number }>({
    mutationFn: async ({ days = 7 }) => {
      // 0. Ensure permissions are granted before reading
      await requestPermissions();

      // 1. Read from Health Connect
      const endTime = new Date();
      const startTime = new Date();
      startTime.setDate(startTime.getDate() - days);

      const payload = await readHealthData(startTime, endTime);

      // 2. POST to backend
      const response = await apiClient.post<SyncResponse>(
        '/api/v1/health-data/sync',
        payload,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health-connect-status'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });
}

export function useRequestHealthPermissions() {
  return useMutation<boolean, Error>({
    mutationFn: async () => {
      return await requestPermissions();
    },
  });
}

export { isHealthConnectAvailable };
