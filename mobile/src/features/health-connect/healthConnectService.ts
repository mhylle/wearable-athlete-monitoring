/**
 * Health Connect SDK integration service.
 *
 * This module wraps the react-native-health-connect library and provides
 * a clean API for reading health data from Google Health Connect.
 *
 * IMPORTANT: Health Connect is only available on Android 8+ and requires
 * a development build (not Expo Go). The service gracefully degrades
 * when Health Connect is unavailable.
 */

import { Platform } from 'react-native';

// Types matching the backend HCSyncRequest schema
export interface HCMetricRecord {
  metric_type: string;
  value: number;
  recorded_at: string; // ISO 8601
}

export interface HCExerciseSession {
  exercise_type: string;
  start_time: string;
  end_time: string | null;
  duration_minutes: number | null;
  hr_avg: number | null;
  hr_max: number | null;
  hr_min: number | null;
  distance_m: number | null;
  energy_kcal: number | null;
  steps: number | null;
  hc_record_id: string | null;
}

export interface HCSyncPayload {
  metrics: HCMetricRecord[];
  exercise_sessions: HCExerciseSession[];
  changes_token: string | null;
}

/**
 * Check if Health Connect is available on this device.
 * Returns false on iOS or when the SDK is not installed.
 */
export function isHealthConnectAvailable(): boolean {
  if (Platform.OS !== 'android') {
    return false;
  }

  try {
    require('react-native-health-connect');
    return true;
  } catch {
    return false;
  }
}

/**
 * Request Health Connect permissions for reading health data.
 * Throws on errors so the caller (mutation onError) can show feedback.
 */
export async function requestPermissions(): Promise<boolean> {
  if (!isHealthConnectAvailable()) {
    throw new Error('Health Connect SDK is not available on this device.');
  }

  const {
    initialize,
    requestPermission,
  } = require('react-native-health-connect') as typeof import('react-native-health-connect');

  await initialize();

  const result = await requestPermission([
    { accessType: 'read', recordType: 'HeartRate' },
    { accessType: 'read', recordType: 'HeartRateVariabilityRmssd' },
    { accessType: 'read', recordType: 'RestingHeartRate' },
    { accessType: 'read', recordType: 'Steps' },
    { accessType: 'read', recordType: 'SleepSession' },
    { accessType: 'read', recordType: 'ExerciseSession' },
    { accessType: 'read', recordType: 'OxygenSaturation' },
    { accessType: 'read', recordType: 'Vo2Max' },
  ]);

  if (result.length === 0) {
    throw new Error('Health Connect permissions were denied. Please grant permissions in Settings.');
  }

  return true;
}

/** Map Health Connect sleep stage constants to our metric suffixes. */
const SLEEP_STAGE_MAP: Record<string, string> = {
  awake: 'sleep_awake',
  sleeping: 'sleep_total',
  light: 'sleep_light',
  deep: 'sleep_deep',
  rem: 'sleep_rem',
  out_of_bed: 'sleep_awake',
};

/**
 * Read health data from Health Connect for the given time range.
 * Returns a sync payload ready to POST to the backend.
 */
export async function readHealthData(
  startTime: Date,
  endTime: Date,
): Promise<HCSyncPayload> {
  const metrics: HCMetricRecord[] = [];
  const exerciseSessions: HCExerciseSession[] = [];

  if (!isHealthConnectAvailable()) {
    return { metrics, exercise_sessions: exerciseSessions, changes_token: null };
  }

  const {
    initialize,
    readRecords,
  } = require('react-native-health-connect') as typeof import('react-native-health-connect');

  await initialize();

  const timeRange = {
    operator: 'between' as const,
    startTime: startTime.toISOString(),
    endTime: endTime.toISOString(),
  };

  // Read heart rate records
  try {
    const hrRecords = await readRecords('HeartRate', { timeRangeFilter: timeRange });
    for (const record of hrRecords.records) {
      for (const sample of (record as any).samples ?? []) {
        metrics.push({
          metric_type: 'heart_rate',
          value: sample.beatsPerMinute,
          recorded_at: sample.time,
        });
      }
    }
  } catch { /* permission may not be granted */ }

  // Read HRV records — backend expects "hrv_rmssd"
  try {
    const hrvRecords = await readRecords('HeartRateVariabilityRmssd', {
      timeRangeFilter: timeRange,
    });
    for (const record of hrvRecords.records) {
      metrics.push({
        metric_type: 'hrv_rmssd',
        value: (record as any).heartRateVariabilityMillis,
        recorded_at: (record as any).time,
      });
    }
  } catch { /* permission may not be granted */ }

  // Read resting heart rate — backend expects "resting_hr"
  try {
    const rhrRecords = await readRecords('RestingHeartRate', {
      timeRangeFilter: timeRange,
    });
    for (const record of rhrRecords.records) {
      metrics.push({
        metric_type: 'resting_hr',
        value: (record as any).beatsPerMinute,
        recorded_at: (record as any).time,
      });
    }
  } catch { /* permission may not be granted */ }

  // Read steps
  try {
    const stepsRecords = await readRecords('Steps', { timeRangeFilter: timeRange });
    for (const record of stepsRecords.records) {
      metrics.push({
        metric_type: 'steps',
        value: (record as any).count,
        recorded_at: (record as any).endTime,
      });
    }
  } catch { /* permission may not be granted */ }

  // Read sleep sessions — extract per-stage durations
  try {
    const sleepRecords = await readRecords('SleepSession', {
      timeRangeFilter: timeRange,
    });
    for (const record of sleepRecords.records) {
      const r = record as any;
      const sessionEnd: string = r.endTime;
      const stages: Array<{ startTime: string; endTime: string; stage: string }> =
        r.stages ?? [];

      if (stages.length > 0) {
        // Accumulate duration per stage type in minutes
        const stageDurations: Record<string, number> = {};
        let totalMinutes = 0;

        for (const stage of stages) {
          const start = new Date(stage.startTime).getTime();
          const end = new Date(stage.endTime).getTime();
          const durationMin = (end - start) / 60000;
          const metricType = SLEEP_STAGE_MAP[stage.stage] ?? 'sleep_light';

          stageDurations[metricType] = (stageDurations[metricType] ?? 0) + durationMin;
          totalMinutes += durationMin;
        }

        // Emit sleep_total as overall duration
        metrics.push({
          metric_type: 'sleep_total',
          value: totalMinutes,
          recorded_at: sessionEnd,
        });

        // Emit individual stage metrics (skip sleep_total since we already emitted it,
        // and skip sleep_awake from the total sleep count)
        for (const [metricType, duration] of Object.entries(stageDurations)) {
          if (metricType !== 'sleep_total') {
            metrics.push({
              metric_type: metricType,
              value: duration,
              recorded_at: sessionEnd,
            });
          }
        }
      } else {
        // No stage data — emit total duration only
        const start = new Date(r.startTime);
        const end = new Date(r.endTime);
        const durationMinutes = (end.getTime() - start.getTime()) / 60000;

        metrics.push({
          metric_type: 'sleep_total',
          value: durationMinutes,
          recorded_at: sessionEnd,
        });
      }
    }
  } catch { /* permission may not be granted */ }

  // Read exercise sessions
  try {
    const exerciseRecords = await readRecords('ExerciseSession', {
      timeRangeFilter: timeRange,
    });
    for (const record of exerciseRecords.records) {
      const r = record as any;
      const start = new Date(r.startTime);
      const end = r.endTime ? new Date(r.endTime) : null;
      const durationMinutes = end
        ? (end.getTime() - start.getTime()) / 60000
        : null;

      exerciseSessions.push({
        exercise_type: r.exerciseType?.toString() ?? 'other',
        start_time: r.startTime,
        end_time: r.endTime ?? null,
        duration_minutes: durationMinutes,
        hr_avg: null,
        hr_max: null,
        hr_min: null,
        distance_m: null,
        energy_kcal: null,
        steps: null,
        hc_record_id: r.metadata?.id ?? null,
      });
    }
  } catch { /* permission may not be granted */ }

  // Read VO2 Max
  try {
    const vo2Records = await readRecords('Vo2Max', { timeRangeFilter: timeRange });
    for (const record of vo2Records.records) {
      metrics.push({
        metric_type: 'vo2max',
        value: (record as any).vo2MillilitersPerMinuteKilogram,
        recorded_at: (record as any).time,
      });
    }
  } catch { /* permission may not be granted */ }

  // Read SpO2
  try {
    const spo2Records = await readRecords('OxygenSaturation', {
      timeRangeFilter: timeRange,
    });
    for (const record of spo2Records.records) {
      metrics.push({
        metric_type: 'spo2',
        value: (record as any).percentage,
        recorded_at: (record as any).time,
      });
    }
  } catch { /* permission may not be granted */ }

  return { metrics, exercise_sessions: exerciseSessions, changes_token: null };
}
