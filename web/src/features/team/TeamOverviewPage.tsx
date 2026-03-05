import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAthletes } from "@/api/hooks/useAthletes";
import {
  useTeamACWROverview,
  useTeamRecoveryOverview,
  useAthleteFitness,
} from "@/api/hooks/useAnalytics";
import { useTeamAnomalies } from "@/api/hooks/useAnomalies";
import { ZoneBadge } from "@/components/ui/ZoneBadge";

type SortField = "name" | "recovery" | "fitness" | "anomalies";

export function TeamOverviewPage() {
  const { data: athletes, isLoading: loadingAthletes } = useAthletes();
  const { data: acwrOverview } = useTeamACWROverview();
  const { data: recoveryOverview } = useTeamRecoveryOverview();
  const { data: anomalies } = useTeamAnomalies();

  const [sortBy, setSortBy] = useState<SortField>("name");
  const [filterZone, setFilterZone] = useState<string>("all");

  const acwrMap = useMemo(() => {
    const map = new Map<string, { zone: "undertraining" | "optimal" | "caution" | "high_risk" }>();
    acwrOverview?.forEach((a) => map.set(a.athlete_id, { zone: a.zone }));
    return map;
  }, [acwrOverview]);

  const recoveryMap = useMemo(() => {
    const map = new Map<string, number>();
    recoveryOverview?.forEach((r) => map.set(r.athlete_id, r.total_score));
    return map;
  }, [recoveryOverview]);

  // We'll gather fitness scores per athlete using individual hooks via a child component
  // For the sort, we track fitness in a simple map populated from AthleteCard renders
  const [fitnessMap, setFitnessMap] = useState<Map<string, number>>(new Map());

  const anomalyCountMap = useMemo(() => {
    const map = new Map<string, number>();
    anomalies?.forEach((a) => {
      map.set(a.athlete_id, (map.get(a.athlete_id) ?? 0) + 1);
    });
    return map;
  }, [anomalies]);

  const filteredAndSorted = useMemo(() => {
    if (!athletes) return [];
    let list = athletes.filter((a) => a.is_active);

    if (filterZone !== "all") {
      list = list.filter((a) => acwrMap.get(a.id)?.zone === filterZone);
    }

    list.sort((a, b) => {
      if (sortBy === "name") return a.full_name.localeCompare(b.full_name);
      if (sortBy === "recovery") {
        return (recoveryMap.get(b.id) ?? 0) - (recoveryMap.get(a.id) ?? 0);
      }
      if (sortBy === "fitness") {
        return (fitnessMap.get(b.id) ?? 0) - (fitnessMap.get(a.id) ?? 0);
      }
      return (anomalyCountMap.get(b.id) ?? 0) - (anomalyCountMap.get(a.id) ?? 0);
    });

    return list;
  }, [athletes, filterZone, sortBy, acwrMap, recoveryMap, fitnessMap, anomalyCountMap]);

  if (loadingAthletes) {
    return <p className="py-12 text-center text-sm text-gray-500">Loading team...</p>;
  }

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Overview</h1>
          <p className="mt-1 text-sm text-gray-500">
            {filteredAndSorted.length} active athletes
          </p>
        </div>

        <div className="flex gap-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortField)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
            aria-label="Sort by"
          >
            <option value="name">Sort by Name</option>
            <option value="recovery">Sort by Recovery</option>
            <option value="fitness">Sort by Fitness</option>
            <option value="anomalies">Sort by Anomalies</option>
          </select>

          <select
            value={filterZone}
            onChange={(e) => setFilterZone(e.target.value)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
            aria-label="Filter by zone"
          >
            <option value="all">All Zones</option>
            <option value="optimal">Optimal</option>
            <option value="caution">Caution</option>
            <option value="high_risk">High Risk</option>
            <option value="undertraining">Undertraining</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredAndSorted.map((athlete) => (
          <AthleteCardWithFitness
            key={athlete.id}
            id={athlete.id}
            name={athlete.full_name}
            position={null}
            recoveryScore={recoveryMap.get(athlete.id) ?? null}
            acwrZone={acwrMap.get(athlete.id)?.zone ?? null}
            anomalyCount={anomalyCountMap.get(athlete.id) ?? 0}
            garminConnected={false}
            onFitnessLoaded={(score) => {
              setFitnessMap((prev) => {
                const next = new Map(prev);
                next.set(athlete.id, score);
                return next;
              });
            }}
          />
        ))}
      </div>

      {filteredAndSorted.length === 0 && (
        <p className="py-12 text-center text-sm text-gray-400">
          No athletes match the current filter.
        </p>
      )}
    </div>
  );
}

function fitnessColor(score: number): string {
  if (score >= 80) return "text-blue-600";
  if (score >= 60) return "text-green-600";
  if (score >= 40) return "text-yellow-600";
  return "text-red-600";
}

function AthleteCardWithFitness({
  id,
  name,
  position,
  recoveryScore,
  acwrZone,
  anomalyCount,
  garminConnected,
  onFitnessLoaded,
}: {
  id: string;
  name: string;
  position: string | null;
  recoveryScore: number | null;
  acwrZone: "undertraining" | "optimal" | "caution" | "high_risk" | null;
  anomalyCount: number;
  garminConnected: boolean;
  onFitnessLoaded: (score: number) => void;
}) {
  const { data: fitness } = useAthleteFitness(id);
  const fitnessTotal = fitness?.fitness_score?.total ?? null;

  // Report fitness score up to parent for sorting
  const reportedRef = React.useRef(false);
  React.useEffect(() => {
    if (fitnessTotal !== null && !reportedRef.current) {
      reportedRef.current = true;
      onFitnessLoaded(fitnessTotal);
    }
  }, [fitnessTotal, onFitnessLoaded]);

  return (
    <Link
      to={`/athletes/${id}`}
      className="block rounded-xl border border-gray-200 bg-white p-5 transition hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">{name}</h3>
          {position && <p className="text-xs text-gray-500">{position}</p>}
        </div>
        {garminConnected ? (
          <span className="inline-flex h-2 w-2 rounded-full bg-green-400" title="Garmin connected" />
        ) : (
          <span className="inline-flex h-2 w-2 rounded-full bg-gray-300" title="Not connected" />
        )}
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div className="flex gap-4">
          {recoveryScore !== null && (
            <div>
              <p className="text-xs text-gray-500">Recovery</p>
              <p className={`text-xl font-bold ${recoveryScore >= 75 ? "text-green-600" : recoveryScore >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                {Math.round(recoveryScore)}
              </p>
            </div>
          )}
          {fitnessTotal !== null && (
            <div>
              <p className="text-xs text-gray-500">Fitness</p>
              <p className={`text-xl font-bold ${fitnessColor(fitnessTotal)}`}>
                {Math.round(fitnessTotal)}
              </p>
            </div>
          )}
          {recoveryScore === null && fitnessTotal === null && (
            <p className="text-xs text-gray-400">No score data</p>
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
