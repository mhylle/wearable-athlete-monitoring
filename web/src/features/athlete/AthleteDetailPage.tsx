import { useParams } from "react-router-dom";
import { useAthlete, useAthleteProfile } from "@/api/hooks/useAthletes";
import {
  useAthleteACWR,
  useAthleteHRV,
  useAthleteSleep,
  useAthleteRecovery,
  useAthleteAvailableMetrics,
  useAthleteMetricSeries,
  useAthleteFitness,
} from "@/api/hooks/useAnalytics";
import { MetricLineChart } from "@/components/charts/MetricLineChart";
import { useAthleteAnomalies } from "@/api/hooks/useAnomalies";
import { useAthleteWellness } from "@/api/hooks/useWellness";
import { ACWRChart } from "@/components/charts/ACWRChart";
import { HRVTrendChart } from "@/components/charts/HRVTrendChart";
import { SleepChart } from "@/components/charts/SleepChart";
import { RecoveryChart } from "@/components/charts/RecoveryChart";
import { ZoneBadge } from "@/components/ui/ZoneBadge";
import { MetricValue } from "@/components/ui/MetricValue";
import { AnomalyCard } from "@/components/ui/AnomalyCard";
import { FitnessScoreCard } from "@/components/cards/FitnessScoreCard";
import { TrendIndicator } from "@/components/ui/TrendIndicator";

const TIME_METRICS = new Set(["sleep_total", "sleep_light"]);

const VITALS_CONFIGS = [
  { key: "heart_rate", label: "Heart Rate", unit: "bpm", color: "#ef4444" },
  { key: "hrv_rmssd", label: "HRV (RMSSD)", unit: "ms", color: "#8b5cf6" },
  { key: "resting_hr", label: "Resting HR", unit: "bpm", color: "#f97316" },
  { key: "steps", label: "Steps", unit: "steps", color: "#22c55e" },
  { key: "sleep_total", label: "Sleep Total", unit: "", color: "#3b82f6" },
  { key: "sleep_light", label: "Sleep Light", unit: "", color: "#a78bfa" },
  { key: "spo2", label: "SpO2", unit: "%", color: "#06b6d4" },
  { key: "vo2_max", label: "VO2 Max", unit: "ml/kg/min", color: "#ec4899" },
];

function VitalCard({ athleteId, metricKey, label, unit, color, trend }: {
  athleteId: string;
  metricKey: string;
  label: string;
  unit: string;
  color: string;
  trend?: "improving" | "stable" | "declining";
}) {
  const { data } = useAthleteMetricSeries(athleteId, metricKey, 30);
  const points = data?.data ?? [];

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-4 flex items-center gap-2">
        <h2 className="text-sm font-semibold text-gray-900">{label} (30-day)</h2>
        {trend && <TrendIndicator direction={trend} />}
      </div>
      <MetricLineChart data={points} label={label} unit={unit} color={color} isTime={TIME_METRICS.has(metricKey)} />
    </section>
  );
}

export function AthleteDetailPage() {
  const { id } = useParams<{ id: string }>();
  const athleteId = id ?? "";

  const { data: athlete, isLoading } = useAthlete(athleteId);
  const { data: profile } = useAthleteProfile(athleteId);
  const { data: acwrData } = useAthleteACWR(athleteId);
  const { data: hrvData } = useAthleteHRV(athleteId);
  const { data: sleepData } = useAthleteSleep(athleteId);
  const { data: recoveryData } = useAthleteRecovery(athleteId);
  const { data: anomalies } = useAthleteAnomalies(athleteId);
  const { data: wellness } = useAthleteWellness(athleteId);
  const { data: availableMetrics } = useAthleteAvailableMetrics(athleteId);
  const { data: fitnessData } = useAthleteFitness(athleteId);

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-gray-500">Loading athlete...</p>;
  }

  if (!athlete) {
    return <p className="py-12 text-center text-sm text-gray-500">Athlete not found</p>;
  }

  const latestACWR = acwrData && acwrData.length > 0 ? acwrData[acwrData.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{athlete.full_name}</h1>
          <div className="mt-1 flex items-center gap-3 text-sm text-gray-500">
            {profile?.position && <span>{profile.position}</span>}
            {profile?.garmin_connected && (
              <span className="inline-flex items-center gap-1 text-green-600">
                <span className="inline-flex h-2 w-2 rounded-full bg-green-400" />
                Garmin connected
              </span>
            )}
          </div>
        </div>
        {latestACWR && <ZoneBadge zone={latestACWR.zone} />}
      </div>

      {/* Fitness Score */}
      {fitnessData && fitnessData.fitness_score.total !== null && (
        <FitnessScoreCard data={fitnessData} />
      )}

      {/* Metrics summary */}
      <div className="grid grid-cols-2 gap-4 rounded-xl border border-gray-200 bg-white p-5 sm:grid-cols-4">
        {recoveryData && (
          <MetricValue label="Recovery Score" value={Math.round(recoveryData.total_score)} />
        )}
        {latestACWR && (
          <MetricValue label="ACWR" value={latestACWR.acwr_value.toFixed(2)} />
        )}
        {hrvData && (
          <MetricValue label="HRV (RMSSD)" value={hrvData.rolling_mean.toFixed(1)} unit="ms" />
        )}
        {hrvData && (
          <MetricValue label="HRV Trend" value={hrvData.trend} />
        )}
      </div>

      {/* Charts grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">ACWR (28-day)</h2>
          <ACWRChart data={acwrData ?? []} />
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">HRV Trend (30-day)</h2>
          {hrvData ? (
            <HRVTrendChart data={hrvData} />
          ) : (
            <p className="py-8 text-center text-sm text-gray-400">No HRV data</p>
          )}
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Sleep (14-day)</h2>
          <SleepChart data={sleepData ?? []} />
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Recovery Score (14-day)</h2>
          <RecoveryChart data={[]} />
        </section>
      </div>

      {/* Vitals */}
      {availableMetrics && availableMetrics.metric_types.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold text-gray-900">Vitals</h2>
          <div className="grid gap-6 lg:grid-cols-2">
            {VITALS_CONFIGS.filter((c) => availableMetrics.metric_types.includes(c.key)).map(
              (config) => {
                const trend = fitnessData?.trends.find((t) => t.metric_type === config.key);
                return (
                  <VitalCard
                    key={config.key}
                    athleteId={athleteId}
                    metricKey={config.key}
                    label={config.label}
                    unit={config.unit}
                    color={config.color}
                    trend={trend?.direction}
                  />
                );
              }
            )}
          </div>
        </section>
      )}

      {/* Anomalies */}
      {anomalies && anomalies.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold text-gray-900">
            Active Anomalies ({anomalies.length})
          </h2>
          <div className="space-y-3">
            {anomalies.map((anomaly, idx) => (
              <AnomalyCard key={idx} anomaly={anomaly} />
            ))}
          </div>
        </section>
      )}

      {/* Wellness table */}
      {wellness && wellness.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Recent Wellness</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Date</th>
                  <th className="pb-2 pr-4 font-medium">sRPE</th>
                  <th className="pb-2 pr-4 font-medium">Soreness</th>
                  <th className="pb-2 pr-4 font-medium">Fatigue</th>
                  <th className="pb-2 pr-4 font-medium">Mood</th>
                  <th className="pb-2 font-medium">Sleep Quality</th>
                </tr>
              </thead>
              <tbody>
                {wellness.slice(0, 14).map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-50">
                    <td className="py-2 pr-4 text-gray-900">
                      {new Date(entry.date).toLocaleDateString()}
                    </td>
                    <td className="py-2 pr-4">{entry.srpe}</td>
                    <td className="py-2 pr-4">{entry.soreness}</td>
                    <td className="py-2 pr-4">{entry.fatigue}</td>
                    <td className="py-2 pr-4">{entry.mood}</td>
                    <td className="py-2">{entry.sleep_quality}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
