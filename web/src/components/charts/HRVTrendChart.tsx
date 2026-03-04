import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HRVAnalysis } from "@/types/api";

interface HRVTrendChartProps {
  data: HRVAnalysis;
}

export function HRVTrendChart({ data }: HRVTrendChartProps) {
  if (!data.daily_values || data.daily_values.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No HRV data available</p>;
  }

  const chartData = data.daily_values.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    rmssd: d.rmssd,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="rmssd"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={false}
          name="RMSSD"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
