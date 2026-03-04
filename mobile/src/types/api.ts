export interface User {
  id: string;
  email: string;
  role: 'coach' | 'athlete';
  full_name: string;
  team_id: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AthleteProfile {
  id: string;
  user_id: string;
  position: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  garmin_connected: boolean;
  health_connect_connected: boolean;
  last_sync_at: string | null;
}

export interface RecoveryScore {
  total_score: number | null;
  hrv_component: number | null;
  sleep_component: number | null;
  load_component: number | null;
  subjective_component: number | null;
  available_components: string[];
}

export interface ACWRResult {
  acute_ewma: number;
  chronic_ewma: number;
  acwr_value: number | null;
  zone: 'undertraining' | 'optimal' | 'caution' | 'high_risk';
  date: string;
}

export interface DailyHRV {
  date: string;
  rmssd: number;
}

export interface HRVStats {
  rolling_mean: number;
  rolling_cv: number;
  trend: 'improving' | 'stable' | 'declining';
  baseline_mean: number;
}

export interface HRVAnalysis {
  athlete_id: string;
  start: string;
  end: string;
  daily_values: DailyHRV[];
  stats: HRVStats;
}

export interface SleepSummary {
  date: string;
  total_minutes: number;
  deep_minutes: number;
  rem_minutes: number;
  light_minutes: number;
  awake_minutes: number;
  efficiency: number;
}

export interface SleepAverage {
  days: number;
  avg_total_minutes: number;
  avg_deep_minutes: number;
  avg_rem_minutes: number;
  avg_light_minutes: number;
  avg_awake_minutes: number;
  avg_efficiency: number;
}

export interface SleepAnalysis {
  athlete_id: string;
  start: string;
  end: string;
  daily_summaries: SleepSummary[];
  average: SleepAverage;
}

export interface Anomaly {
  athlete_id: string;
  metric_type: string;
  value: number;
  expected_median: number;
  mad_score: number;
  severity: 'low' | 'medium' | 'high';
  anomaly_type: 'spike' | 'drop' | 'trend_break';
  explanation: string;
  detected_at: string;
}

export interface AnomaliesResponse {
  athlete_id: string;
  anomalies: Anomaly[];
  date: string;
}

export interface Session {
  id: string;
  athlete_id: string;
  source: string;
  session_type: string;
  start_time: string;
  duration_minutes: number;
  hr_avg: number | null;
  hr_max: number | null;
  distance_meters: number | null;
  calories: number | null;
}

export interface WellnessEntry {
  id: string;
  athlete_id: string;
  date: string;
  srpe: number;
  session_duration_minutes: number | null;
  soreness: number;
  fatigue: number;
  mood: number;
  sleep_quality: number;
  notes: string | null;
}

export interface WellnessSubmission {
  srpe: number;
  session_duration_minutes: number;
  soreness: number;
  fatigue: number;
  mood: number;
  sleep_quality: number;
  notes?: string;
}
