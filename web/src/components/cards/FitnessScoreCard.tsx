import { FitnessScoreGauge } from "@/components/charts/FitnessScoreGauge";
import { TrendIndicator } from "@/components/ui/TrendIndicator";
import type { AthleteFitness } from "@/types/api";

interface FitnessScoreCardProps {
  data: AthleteFitness;
}

const METRIC_LABELS: Record<string, string> = {
  hrv_rmssd: "HRV (RMSSD)",
  resting_heart_rate: "Resting HR",
  sleep_total: "Sleep Duration",
  sleep_quality: "Sleep Quality",
  steps: "Steps",
};

export function FitnessScoreCard({ data }: FitnessScoreCardProps) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Fitness Score</h2>
        <span className="text-xs text-gray-400">
          {new Date(data.fitness_score.computed_at).toLocaleString()}
        </span>
      </div>

      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <FitnessScoreGauge fitness={data.fitness_score} />

        {data.trends.length > 0 && (
          <div className="flex flex-1 flex-col gap-2">
            <h3 className="text-xs font-medium text-gray-500">Metric Trends</h3>
            {data.trends.map((trend) => (
              <div key={trend.metric_type} className="flex items-center justify-between gap-2">
                <span className="text-sm text-gray-700">
                  {METRIC_LABELS[trend.metric_type] ?? trend.metric_type}
                </span>
                <div className="flex items-center gap-2">
                  <TrendIndicator direction={trend.direction} />
                  {trend.is_anomaly && (
                    <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-700">
                      Anomaly
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
