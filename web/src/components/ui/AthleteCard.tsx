import { Link } from "react-router-dom";
import { ZoneBadge } from "@/components/ui/ZoneBadge";

function recoveryColor(score: number): string {
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-600";
}

interface AthleteCardProps {
  id: string;
  name: string;
  position: string | null;
  recoveryScore: number | null;
  acwrZone: "undertraining" | "optimal" | "caution" | "high_risk" | null;
  anomalyCount: number;
  garminConnected: boolean;
}

export function AthleteCard({
  id,
  name,
  position,
  recoveryScore,
  acwrZone,
  anomalyCount,
  garminConnected,
}: AthleteCardProps) {
  return (
    <Link
      to={`/athletes/${id}`}
      className="block rounded-xl border border-gray-200 bg-white p-5 transition hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{name}</h3>
          {position && (
            <p className="text-xs text-gray-500">{position}</p>
          )}
        </div>
        {garminConnected ? (
          <span className="inline-flex h-2 w-2 rounded-full bg-green-400" title="Garmin connected" />
        ) : (
          <span className="inline-flex h-2 w-2 rounded-full bg-gray-300" title="Garmin not connected" />
        )}
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div>
          {recoveryScore !== null ? (
            <div>
              <p className="text-xs text-gray-500">Recovery</p>
              <p className={`text-2xl font-bold ${recoveryColor(recoveryScore)}`}>
                {Math.round(recoveryScore)}
              </p>
            </div>
          ) : (
            <p className="text-xs text-gray-400">No recovery data</p>
          )}
        </div>

        <div className="flex flex-col items-end gap-1.5">
          {acwrZone && <ZoneBadge zone={acwrZone} />}
          {anomalyCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
              {anomalyCount} {anomalyCount === 1 ? "anomaly" : "anomalies"}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
