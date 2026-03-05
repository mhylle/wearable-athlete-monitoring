interface TrendIndicatorProps {
  direction: "improving" | "stable" | "declining";
  label?: string;
  size?: "sm" | "md";
}

const config = {
  improving: { arrow: "\u2191", color: "text-green-600", bg: "bg-green-50", label: "Improving" },
  stable: { arrow: "\u2192", color: "text-gray-500", bg: "bg-gray-50", label: "Stable" },
  declining: { arrow: "\u2193", color: "text-red-600", bg: "bg-red-50", label: "Declining" },
};

export function TrendIndicator({ direction, label, size = "sm" }: TrendIndicatorProps) {
  const cfg = config[direction];
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${cfg.bg} ${cfg.color} ${textSize} font-medium`}
    >
      <span>{cfg.arrow}</span>
      {label ?? cfg.label}
    </span>
  );
}
