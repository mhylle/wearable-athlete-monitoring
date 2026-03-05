import type { FitnessScore } from "@/types/api";

const COMPONENT_LABELS: Record<string, string> = {
  hrv_rmssd: "HRV",
  resting_heart_rate: "Resting HR",
  sleep_total: "Sleep",
  sleep_quality: "Sleep Quality",
  steps: "Steps",
  hrv_balance: "HRV Balance",
  trend_bonus: "Trend Bonus",
};

const COMPONENT_COLORS: Record<string, string> = {
  hrv_rmssd: "#8b5cf6",
  resting_heart_rate: "#f97316",
  sleep_total: "#3b82f6",
  sleep_quality: "#06b6d4",
  steps: "#22c55e",
  hrv_balance: "#ec4899",
  trend_bonus: "#f59e0b",
};

function scoreColor(score: number): string {
  if (score >= 80) return "#3b82f6";
  if (score >= 60) return "#22c55e";
  if (score >= 40) return "#eab308";
  return "#ef4444";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Poor";
}

interface FitnessScoreGaugeProps {
  fitness: FitnessScore;
  size?: number;
}

export function FitnessScoreGauge({ fitness, size = 160 }: FitnessScoreGaugeProps) {
  const score = fitness.total ?? 0;
  const color = scoreColor(score);
  const label = scoreLabel(score);

  // SVG arc params
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - 20) / 2;
  const circumference = Math.PI * r; // semi-circle
  const progress = (score / 100) * circumference;

  // Arc path (semi-circle, bottom open)
  const startAngle = Math.PI;
  const endAngle = 2 * Math.PI;

  function polarToCartesian(angle: number) {
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  }

  const start = polarToCartesian(startAngle);
  const end = polarToCartesian(endAngle);
  const arcPath = `M ${start.x} ${start.y} A ${r} ${r} 0 0 1 ${end.x} ${end.y}`;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
        {/* Background arc */}
        <path
          d={arcPath}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={10}
          strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={arcPath}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          className="transition-all duration-700"
        />
        {/* Score text */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          className="text-3xl font-bold"
          fill={color}
          fontSize={size * 0.2}
        >
          {fitness.total !== null ? Math.round(score) : "—"}
        </text>
        <text
          x={cx}
          y={cy + size * 0.1}
          textAnchor="middle"
          fill="#6b7280"
          fontSize={size * 0.08}
        >
          {label}
        </text>
      </svg>

      {/* Component breakdown bar */}
      {fitness.available_components.length > 0 && (
        <div className="mt-2 w-full">
          <div className="flex h-2 overflow-hidden rounded-full">
            {fitness.available_components.map((comp) => {
              const value = fitness.components[comp] ?? 0;
              const pct = value / 100;
              return (
                <div
                  key={comp}
                  className="transition-all duration-500"
                  style={{
                    width: `${(1 / fitness.available_components.length) * 100}%`,
                    backgroundColor: COMPONENT_COLORS[comp] ?? "#9ca3af",
                    opacity: 0.3 + pct * 0.7,
                  }}
                  title={`${COMPONENT_LABELS[comp] ?? comp}: ${Math.round(value)}`}
                />
              );
            })}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
            {fitness.available_components.map((comp) => (
              <div key={comp} className="flex items-center gap-1 text-xs text-gray-500">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ backgroundColor: COMPONENT_COLORS[comp] ?? "#9ca3af" }}
                />
                {COMPONENT_LABELS[comp] ?? comp}: {Math.round(fitness.components[comp] ?? 0)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
