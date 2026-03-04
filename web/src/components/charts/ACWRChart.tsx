import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ResponsiveContainer,
} from "recharts";
import type { ACWRResult } from "@/types/api";

interface ACWRChartProps {
  data: ACWRResult[];
}

export function ACWRChart({ data }: ACWRChartProps) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No ACWR data available</p>;
  }

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString("da-DK", { day: "numeric", month: "short" }),
    acwr: d.acwr_value,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        {/* Zone bands */}
        <ReferenceArea y1={0} y2={0.8} fill="#dbeafe" fillOpacity={0.3} />
        <ReferenceArea y1={0.8} y2={1.3} fill="#dcfce7" fillOpacity={0.3} />
        <ReferenceArea y1={1.3} y2={1.5} fill="#fef9c3" fillOpacity={0.3} />
        <ReferenceArea y1={1.5} y2={2.5} fill="#fed7aa" fillOpacity={0.3} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 2.5]} tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="acwr"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
          name="ACWR"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
