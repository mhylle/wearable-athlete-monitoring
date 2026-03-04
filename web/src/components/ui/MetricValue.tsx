interface MetricValueProps {
  label: string;
  value: string | number;
  unit?: string;
  className?: string;
}

export function MetricValue({ label, value, unit, className }: MetricValueProps) {
  return (
    <div className={className}>
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900">
        {value}
        {unit && <span className="ml-0.5 text-sm font-normal text-gray-500">{unit}</span>}
      </p>
    </div>
  );
}
