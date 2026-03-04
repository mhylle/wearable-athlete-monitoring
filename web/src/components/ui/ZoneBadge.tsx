const zoneConfig = {
  optimal: { label: "Optimal", className: "bg-green-100 text-green-800" },
  caution: { label: "Caution", className: "bg-yellow-100 text-yellow-800" },
  high_risk: { label: "High Risk", className: "bg-orange-100 text-orange-800" },
  undertraining: {
    label: "Undertraining",
    className: "bg-blue-100 text-blue-800",
  },
} as const;

interface ZoneBadgeProps {
  zone: keyof typeof zoneConfig;
}

export function ZoneBadge({ zone }: ZoneBadgeProps) {
  const config = zoneConfig[zone];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}
