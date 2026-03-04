import { useParams } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useAthlete } from "@/api/hooks/useAthletes";
import { useAthleteWellness } from "@/api/hooks/useWellness";

const METRIC_CONFIGS = [
  { key: "mood", label: "Mood", color: "#2563eb" },
  { key: "soreness", label: "Soreness", color: "#dc2626" },
  { key: "fatigue", label: "Fatigue", color: "#f59e0b" },
  { key: "sleep_quality", label: "Sleep Quality", color: "#8b5cf6" },
  { key: "srpe", label: "sRPE", color: "#059669" },
] as const;

type MetricKey = (typeof METRIC_CONFIGS)[number]["key"];

export function AthleteWellnessDetail() {
  const { athleteId } = useParams<{ athleteId: string }>();
  const id = athleteId ?? "";

  const { data: athlete } = useAthlete(id);
  const { data: wellness, isLoading } = useAthleteWellness(id);

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-gray-500">Loading wellness data...</p>;
  }

  const entries = wellness ?? [];
  const sortedEntries = [...entries].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const chartData = sortedEntries.map((e) => ({
    date: new Date(e.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    mood: e.mood,
    soreness: e.soreness,
    fatigue: e.fatigue,
    sleep_quality: e.sleep_quality,
    srpe: e.srpe,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {athlete?.full_name ?? "Athlete"} - Wellness
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {entries.length} wellness entries
        </p>
      </div>

      {/* Trend charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {METRIC_CONFIGS.map((config) => (
          <section
            key={config.key}
            className="rounded-xl border border-gray-200 bg-white p-5"
          >
            <h2 className="mb-4 text-sm font-semibold text-gray-900">
              {config.label} Trend
            </h2>
            {chartData.length === 0 ? (
              <p className="py-8 text-center text-sm text-gray-400">No data</p>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey={config.key as MetricKey}
                    stroke={config.color}
                    strokeWidth={2}
                    dot={false}
                    name={config.label}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </section>
        ))}
      </div>

      {/* History table */}
      {entries.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Wellness History</h2>
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
                {[...entries]
                  .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                  .map((entry) => (
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
