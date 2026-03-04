import { useMemo, useState } from "react";
import { useAthletes } from "@/api/hooks/useAthletes";
import {
  useTeamACWROverview,
  useTeamRecoveryOverview,
} from "@/api/hooks/useAnalytics";
import { useTeamAnomalies } from "@/api/hooks/useAnomalies";
import { AthleteCard } from "@/components/ui/AthleteCard";

type SortField = "name" | "recovery" | "anomalies";

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
      return (anomalyCountMap.get(b.id) ?? 0) - (anomalyCountMap.get(a.id) ?? 0);
    });

    return list;
  }, [athletes, filterZone, sortBy, acwrMap, recoveryMap, anomalyCountMap]);

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
          <AthleteCard
            key={athlete.id}
            id={athlete.id}
            name={athlete.full_name}
            position={null}
            recoveryScore={recoveryMap.get(athlete.id) ?? null}
            acwrZone={acwrMap.get(athlete.id)?.zone ?? null}
            anomalyCount={anomalyCountMap.get(athlete.id) ?? 0}
            garminConnected={false}
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
