import { Link } from "react-router-dom";
import { useAthletes } from "@/api/hooks/useAthletes";
import { useTeamWellnessOverview } from "@/api/hooks/useWellness";

export function WellnessOverviewPage() {
  const { data: athletes, isLoading: loadingAthletes } = useAthletes();
  const { data: wellnessStatus } = useTeamWellnessOverview();

  const statusMap = new Map(
    wellnessStatus?.map((w) => [w.athlete_id, w]) ?? []
  );

  if (loadingAthletes) {
    return <p className="py-12 text-center text-sm text-gray-500">Loading...</p>;
  }

  const activeAthletes = athletes?.filter((a) => a.is_active) ?? [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Wellness Overview</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track athlete wellness submissions and trends.
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50 text-xs text-gray-500">
              <th className="px-4 py-3 font-medium">Athlete</th>
              <th className="px-4 py-3 font-medium">Today's Status</th>
              <th className="px-4 py-3 font-medium">Mood</th>
              <th className="px-4 py-3 font-medium">Soreness</th>
              <th className="px-4 py-3 font-medium">Fatigue</th>
              <th className="px-4 py-3 font-medium">sRPE</th>
              <th className="px-4 py-3 font-medium">Sleep Quality</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {activeAthletes.map((athlete) => {
              const status = statusMap.get(athlete.id);
              const submitted = status?.submitted ?? false;
              const entry = status?.latest_entry;

              return (
                <tr key={athlete.id} className="border-b border-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {athlete.full_name}
                  </td>
                  <td className="px-4 py-3">
                    {submitted ? (
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Submitted
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                        Not submitted
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">{entry?.mood ?? "-"}</td>
                  <td className="px-4 py-3">{entry?.soreness ?? "-"}</td>
                  <td className="px-4 py-3">{entry?.fatigue ?? "-"}</td>
                  <td className="px-4 py-3">{entry?.srpe ?? "-"}</td>
                  <td className="px-4 py-3">{entry?.sleep_quality ?? "-"}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/wellness/${athlete.id}`}
                      className="text-sm font-medium text-blue-600 hover:text-blue-800"
                    >
                      View detail
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {activeAthletes.length === 0 && (
        <p className="py-12 text-center text-sm text-gray-400">No active athletes.</p>
      )}
    </div>
  );
}
