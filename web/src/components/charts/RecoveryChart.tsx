import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface RecoveryDataPoint {
  date: string;
  score: number;
}

interface RecoveryChartProps {
  data: RecoveryDataPoint[];
}

export function RecoveryChart({ data }: RecoveryChartProps) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No recovery data available</p>;
  }

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("da-DK", { day: "numeric", month: "short" }),
    score: d.score,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
        <Tooltip />
        <ReferenceLine y={75} stroke="#22c55e" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#eab308" strokeDasharray="3 3" />
        <Line
          type="monotone"
          dataKey="score"
          stroke="#059669"
          strokeWidth={2}
          dot={false}
          name="Recovery Score"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
