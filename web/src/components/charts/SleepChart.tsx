import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { SleepSummary } from "@/types/api";

interface SleepChartProps {
  data: SleepSummary[];
}

export function SleepChart({ data }: SleepChartProps) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No sleep data available</p>;
  }

  const chartData = data.map((d) => {
    const lightMinutes = d.total_minutes - d.deep_minutes - d.rem_minutes;
    return {
      date: new Date(d.date).toLocaleDateString("da-DK", { day: "numeric", month: "short" }),
      deep: Math.round(d.deep_minutes / 60 * 10) / 10,
      rem: Math.round(d.rem_minutes / 60 * 10) / 10,
      light: Math.round(Math.max(0, lightMinutes) / 60 * 10) / 10,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} label={{ value: "Hours", angle: -90, position: "insideLeft", style: { fontSize: 11 } }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="deep" stackId="sleep" fill="#1e40af" name="Deep" />
        <Bar dataKey="rem" stackId="sleep" fill="#7c3aed" name="REM" />
        <Bar dataKey="light" stackId="sleep" fill="#93c5fd" name="Light" />
      </BarChart>
    </ResponsiveContainer>
  );
}
