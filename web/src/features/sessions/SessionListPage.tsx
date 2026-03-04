import { useMemo, useState } from "react";
import { useAthletes } from "@/api/hooks/useAthletes";
import { useAthleteSessions } from "@/api/hooks/useSessions";

export function SessionListPage() {
  const { data: athletes } = useAthletes();
  const [selectedAthlete, setSelectedAthlete] = useState<string>("");
  const [sessionType, setSessionType] = useState<string>("");
  const [source, setSource] = useState<string>("");

  const filters = useMemo(
    () => ({
      ...(sessionType ? { session_type: sessionType } : {}),
      ...(source ? { source } : {}),
    }),
    [sessionType, source]
  );

  const athleteId = selectedAthlete || (athletes?.[0]?.id ?? "");
  const { data: sessions, isLoading } = useAthleteSessions(athleteId, filters);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
        <p className="mt-1 text-sm text-gray-500">View training and activity sessions</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-3">
        <select
          value={selectedAthlete}
          onChange={(e) => setSelectedAthlete(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Select athlete"
        >
          <option value="">Select Athlete</option>
          {athletes?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.full_name}
            </option>
          ))}
        </select>

        <select
          value={sessionType}
          onChange={(e) => setSessionType(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Session type"
        >
          <option value="">All Types</option>
          <option value="running">Running</option>
          <option value="cycling">Cycling</option>
          <option value="strength">Strength</option>
          <option value="other">Other</option>
        </select>

        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm"
          aria-label="Source"
        >
          <option value="">All Sources</option>
          <option value="garmin">Garmin</option>
          <option value="manual">Manual</option>
        </select>
      </div>

      {/* Sessions table */}
      {!athleteId ? (
        <p className="py-12 text-center text-sm text-gray-400">
          Select an athlete to view sessions.
        </p>
      ) : isLoading ? (
        <p className="py-12 text-center text-sm text-gray-500">Loading sessions...</p>
      ) : !sessions || sessions.length === 0 ? (
        <p className="py-12 text-center text-sm text-gray-400">No sessions found.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50 text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} className="border-b border-gray-50">
                  <td className="px-4 py-3 text-gray-900">
                    {new Date(session.start_time).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 capitalize">{session.session_type}</td>
                  <td className="px-4 py-3 capitalize">{session.source}</td>
                  <td className="px-4 py-3">{session.duration_minutes} min</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
