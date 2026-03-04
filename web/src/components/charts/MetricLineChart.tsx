import {
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";

interface MetricDataPoint {
  date: string;
  avg: number;
  min: number;
  max: number;
}

interface MetricLineChartProps {
  data: MetricDataPoint[];
  label: string;
  unit: string;
  color: string;
  isTime?: boolean;
}

function formatMinutes(minutes: number): string {
  const totalSeconds = Math.round(minutes * 60);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function MetricLineChart({ data, label, unit, color, isTime }: MetricLineChartProps) {
  if (!data || data.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-400">
        No {label.toLowerCase()} data available
      </p>
    );
  }

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    avg: d.avg,
    min: d.min,
    max: d.max,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart
        data={chartData}
        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(value) => [
            isTime
              ? formatMinutes(Number(value))
              : `${Number(value).toFixed(1)} ${unit}`,
            "",
          ]}
          labelStyle={{ fontWeight: 600 }}
        />
        <Area
          type="monotone"
          dataKey="max"
          fill={color}
          fillOpacity={0.08}
          stroke="none"
        />
        <Area
          type="monotone"
          dataKey="min"
          fill="#ffffff"
          fillOpacity={1}
          stroke="none"
        />
        <Line
          type="monotone"
          dataKey="avg"
          stroke={color}
          strokeWidth={2}
          dot={false}
          name={label}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
