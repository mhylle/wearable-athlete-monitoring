import { useAuth } from "@/auth/AuthProvider";
import {
  useAthleteAvailableMetrics,
  useAthleteMetricSeries,
} from "@/api/hooks/useAnalytics";
import { MetricLineChart } from "@/components/charts/MetricLineChart";

interface MetricConfig {
  key: string;
  label: string;
  unit: string;
  color: string;
}

const METRIC_CONFIGS: MetricConfig[] = [
  { key: "heart_rate", label: "Heart Rate", unit: "bpm", color: "#ef4444" },
  { key: "hrv_rmssd", label: "HRV (RMSSD)", unit: "ms", color: "#8b5cf6" },
  { key: "resting_hr", label: "Resting HR", unit: "bpm", color: "#f97316" },
  { key: "steps", label: "Steps", unit: "steps", color: "#22c55e" },
  { key: "sleep_total", label: "Sleep Total", unit: "min", color: "#3b82f6" },
  { key: "sleep_light", label: "Sleep Light", unit: "min", color: "#a78bfa" },
  { key: "spo2", label: "SpO2", unit: "%", color: "#06b6d4" },
  { key: "vo2_max", label: "VO2 Max", unit: "ml/kg/min", color: "#ec4899" },
];

function VitalCard({ athleteId, config }: { athleteId: string; config: MetricConfig }) {
  const { data } = useAthleteMetricSeries(athleteId, config.key, 30);
  const points = data?.data ?? [];

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5">
      <h2 className="mb-4 text-sm font-semibold text-gray-900">{config.label}</h2>
      <MetricLineChart
        data={points}
        label={config.label}
        unit={config.unit}
        color={config.color}
      />
    </section>
  );
}

export function MyVitalsPage() {
  const { user } = useAuth();
  const userId = user?.id ?? "";
  const { data: available, isLoading } = useAthleteAvailableMetrics(userId);

  const availableTypes = available?.metric_types ?? [];
  const visibleMetrics = METRIC_CONFIGS.filter((c) => availableTypes.includes(c.key));

  if (isLoading) {
    return (
      <p className="py-12 text-center text-sm text-gray-500">Loading vitals...</p>
    );
  }

  if (visibleMetrics.length === 0) {
    return (
      <div className="py-12 text-center">
        <h2 className="text-lg font-semibold text-gray-900">No Vitals Data Yet</h2>
        <p className="mt-2 text-sm text-gray-500">
          Sync health data from the mobile app to see your vitals here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Vitals</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        {visibleMetrics.map((config) => (
          <VitalCard key={config.key} athleteId={userId} config={config} />
        ))}
      </div>
    </div>
  );
}
