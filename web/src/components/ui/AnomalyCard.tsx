import type { Anomaly } from "@/types/api";

const severityConfig = {
  low: { className: "bg-yellow-100 text-yellow-800" },
  medium: { className: "bg-orange-100 text-orange-800" },
  high: { className: "bg-red-100 text-red-800" },
} as const;

interface AnomalyCardProps {
  anomaly: Anomaly;
  showAthlete?: boolean;
  athleteName?: string;
}

export function AnomalyCard({ anomaly, showAthlete, athleteName }: AnomalyCardProps) {
  const severity = severityConfig[anomaly.severity];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${severity.className}`}
          >
            {anomaly.severity}
          </span>
          <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
            {anomaly.anomaly_type}
          </span>
        </div>
        <time className="text-xs text-gray-400">
          {new Date(anomaly.detected_at).toLocaleDateString()}
        </time>
      </div>

      {showAthlete && athleteName && (
        <p className="mt-1.5 text-xs font-medium text-gray-700">{athleteName}</p>
      )}

      <p className="mt-2 text-sm text-gray-900">{anomaly.explanation}</p>

      <div className="mt-3 flex gap-4 text-xs text-gray-500">
        <span>Metric: {anomaly.metric_type}</span>
        <span>Value: {anomaly.value.toFixed(1)}</span>
        <span>Expected: {anomaly.expected_median.toFixed(1)}</span>
      </div>
    </div>
  );
}
