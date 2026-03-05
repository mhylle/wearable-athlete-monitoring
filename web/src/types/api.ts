export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Athlete {
  id: string;
  email: string;
  full_name: string;
  role: string;
  team_id: string;
  is_active: boolean;
}

export interface AthleteProfile {
  id: string;
  user_id: string;
  position: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  garmin_connected: boolean;
}

export interface ACWRResult {
  acute_ewma: number;
  chronic_ewma: number;
  acwr_value: number;
  zone: "undertraining" | "optimal" | "caution" | "high_risk";
  date: string;
}

export interface DailyHRV {
  date: string;
  rmssd: number;
}

export interface HRVAnalysis {
  rolling_mean: number;
  rolling_cv: number;
  trend: "improving" | "stable" | "declining";
  baseline_mean: number;
  daily_values: DailyHRV[];
}

export interface SleepSummary {
  date: string;
  total_minutes: number;
  deep_minutes: number;
  rem_minutes: number;
  efficiency: number;
}

export interface RecoveryScore {
  total_score: number;
  hrv_component: number;
  sleep_component: number;
  load_component: number;
  subjective_component: number;
}

export interface Anomaly {
  athlete_id: string;
  metric_type: string;
  value: number;
  expected_median: number;
  mad_score: number;
  severity: "low" | "medium" | "high";
  anomaly_type: "spike" | "drop" | "trend_break";
  explanation: string;
  detected_at: string;
}

export interface Session {
  id: string;
  athlete_id: string;
  source: string;
  session_type: string;
  start_time: string;
  duration_minutes: number;
}

export interface WellnessEntry {
  id: string;
  athlete_id: string;
  date: string;
  srpe: number;
  soreness: number;
  fatigue: number;
  mood: number;
  sleep_quality: number;
}

export interface CreateSessionPayload {
  athlete_id: string;
  session_type: string;
  start_time: string;
  duration_minutes: number;
  source: string;
  notes?: string;
  distance_meters?: number;
  avg_heart_rate?: number;
  max_heart_rate?: number;
}

export interface TeamWellnessStatus {
  athlete_id: string;
  athlete_name: string;
  submitted: boolean;
  latest_entry: WellnessEntry | null;
}

export interface TrainingLoadSummary {
  athlete_id: string;
  acute_load: number;
  chronic_load: number;
  acwr: number;
  zone: string;
}

export interface TeamACWROverview {
  athlete_id: string;
  athlete_name: string;
  acwr_value: number;
  zone: "undertraining" | "optimal" | "caution" | "high_risk";
}

export interface TeamRecoveryOverview {
  athlete_id: string;
  athlete_name: string;
  total_score: number;
}

// Fitness Score & Trends

export interface TrendResult {
  metric_type: string;
  direction: "improving" | "stable" | "declining";
  z_score: number;
  is_anomaly: boolean;
  window_days: number;
}

export interface FitnessScore {
  total: number | null;
  components: Record<string, number>;
  available_components: string[];
  computed_at: string;
}

export interface AthleteFitness {
  athlete_id: string;
  fitness_score: FitnessScore;
  trends: TrendResult[];
  date: string;
}

export interface TeamAthleteFitness {
  athlete_id: string;
  full_name: string;
  fitness_score: FitnessScore;
  trends: TrendResult[];
}

export interface TeamFitness {
  athletes: TeamAthleteFitness[];
  date: string;
}

// LLM Analysis

export interface LLMAnalysisState {
  status: "pending" | "streaming" | "complete" | "error";
  text: string;
  cached?: boolean;
}
