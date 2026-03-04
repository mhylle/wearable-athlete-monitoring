import { useMemo, useState } from "react";
import { useTeamAnomalies } from "@/api/hooks/useAnomalies";
import { useAthletes } from "@/api/hooks/useAthletes";
import { AnomalyCard } from "@/components/ui/AnomalyCard";

export function AnomalyFeed() {
  const { data: anomalies, isLoading } = useTeamAnomalies();
  const { data: athletes } = useAthletes();

  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [athleteFilter, setAthleteFilter] = useState<string>("all");
  const [metricFilter, setMetricFilter] = useState<string>("all");

  const athleteNameMap = useMemo(() => {
    const map = new Map<string, string>();
    athletes?.forEach((a) => map.set(a.id, a.full_name));
    return map;
  }, [athletes]);

  const metricTypes = useMemo(() => {
    if (!anomalies) return [];
    return [...new Set(anomalies.map((a) => a.metric_type))].sort();
  }, [anomalies]);

  const filtered = useMemo(() => {
    if (!anomalies) return [];
    let list = [...anomalies];

    if (severityFilter !== "all") {
      list = list.filter((a) => a.severity === severityFilter);
    }
    if (athleteFilter !== "all") {
      list = list.filter((a) => a.athlete_id === athleteFilter);
    }
    if (metricFilter !== "all") {
      list = list.filter((a) => a.metric_type === metricFilter);
    }

    // Sort by severity (high first), then recency
    const severityOrder = { high: 0, medium: 1, low: 2 };
    list.sort((a, b) => {
      const sevDiff = severityOrder[a.severity] - severityOrder[b.severity];
      if (sevDiff !== 0) return sevDiff;
      return new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime();
    });

    return list;
  }, [anomalies, severityFilter, athleteFilter, metricFilter]);

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-gray-500">Loading anomalies...</p>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Anomaly Feed</h1>
        <p className="mt-1 text-sm text-gray-500">
          {filtered.length} anomalies detected across the team
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-3">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Filter by severity"
        >
          <option value="all">All Severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={athleteFilter}
          onChange={(e) => setAthleteFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Filter by athlete"
        >
          <option value="all">All Athletes</option>
          {athletes?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.full_name}
            </option>
          ))}
        </select>

        <select
          value={metricFilter}
          onChange={(e) => setMetricFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Filter by metric"
        >
          <option value="all">All Metrics</option>
          {metricTypes.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Anomaly list */}
      {filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-gray-400">
          No anomalies match the current filters.
        </p>
      ) : (
        <div className="space-y-3">
          {filtered.map((anomaly, idx) => (
            <AnomalyCard
              key={idx}
              anomaly={anomaly}
              showAthlete
              athleteName={athleteNameMap.get(anomaly.athlete_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
