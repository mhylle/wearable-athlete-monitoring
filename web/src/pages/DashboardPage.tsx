import { useAuth } from "@/auth/AuthProvider";

const comingSoonCards = [
  {
    title: "Team Overview",
    description: "View team-wide performance metrics and trends",
  },
  {
    title: "Training Sessions",
    description: "Monitor real-time and historical session data",
  },
  {
    title: "Wellness Reports",
    description: "Track athlete wellness and readiness scores",
  },
  {
    title: "Analytics",
    description: "Advanced performance analytics and insights",
  },
  {
    title: "Anomaly Detection",
    description: "AI-powered anomaly alerts and notifications",
  },
  {
    title: "Wearable Data",
    description: "Live biometric data from connected devices",
  },
];

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(" ")[0] ?? "Coach"}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Here is an overview of your athlete monitoring dashboard.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {comingSoonCards.map((card) => (
          <div
            key={card.title}
            className="rounded-xl border border-gray-200 bg-white p-6"
          >
            <h3 className="text-sm font-semibold text-gray-900">
              {card.title}
            </h3>
            <p className="mt-1 text-sm text-gray-500">{card.description}</p>
            <span className="mt-4 inline-block rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-500">
              Coming Soon
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
