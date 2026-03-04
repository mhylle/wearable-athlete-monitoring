import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthlete: () => ({
    data: { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
    isLoading: false,
  }),
  useAthleteProfile: () => ({
    data: { id: "p1", user_id: "a1", position: "Midfielder", height_cm: 175, weight_kg: 70, garmin_connected: true },
  }),
}));

vi.mock("@/api/hooks/useAnalytics", () => ({
  useAthleteACWR: () => ({
    data: [
      { acute_ewma: 300, chronic_ewma: 280, acwr_value: 1.07, zone: "optimal", date: "2026-02-27" },
    ],
  }),
  useAthleteHRV: () => ({
    data: {
      rolling_mean: 55.2,
      rolling_cv: 0.12,
      trend: "stable",
      baseline_mean: 52.0,
      history: [{ date: "2026-02-27", rmssd_value: 55 }],
    },
  }),
  useAthleteSleep: () => ({
    data: [
      { date: "2026-02-27", total_minutes: 480, deep_minutes: 90, rem_minutes: 120, efficiency: 0.92 },
    ],
  }),
  useAthleteRecovery: () => ({
    data: { total_score: 78, hrv_component: 20, sleep_component: 22, load_component: 18, subjective_component: 18 },
  }),
}));

vi.mock("@/api/hooks/useAnomalies", () => ({
  useAthleteAnomalies: () => ({
    data: [
      { athlete_id: "a1", metric_type: "hrv", value: 30, expected_median: 55, mad_score: 3.2, severity: "medium", anomaly_type: "drop", explanation: "HRV below baseline", detected_at: "2026-02-27T08:00:00Z" },
    ],
  }),
}));

vi.mock("@/api/hooks/useWellness", () => ({
  useAthleteWellness: () => ({
    data: [
      { id: "w1", athlete_id: "a1", date: "2026-02-27", srpe: 450, soreness: 3, fatigue: 4, mood: 7, sleep_quality: 8 },
    ],
  }),
}));

// Mock recharts to avoid canvas/SVG rendering issues in JSDOM
vi.mock("recharts", () => {
  const MockChart = ({ children }: { children?: React.ReactNode }) => <div data-testid="mock-chart">{children}</div>;
  return {
    LineChart: MockChart,
    BarChart: MockChart,
    Line: () => null,
    Bar: () => null,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
    ReferenceArea: () => null,
    ReferenceLine: () => null,
  };
});

function renderAthleteDetail() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/athletes/a1"]}>
        <Routes>
          <Route path="/athletes/:id" element={<AthleteDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

import { AthleteDetailPage } from "@/features/athlete/AthleteDetailPage";

describe("AthleteDetailPage", () => {
  it("renders athlete name", () => {
    renderAthleteDetail();
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("renders position", () => {
    renderAthleteDetail();
    expect(screen.getByText("Midfielder")).toBeInTheDocument();
  });

  it("shows Garmin status", () => {
    renderAthleteDetail();
    expect(screen.getByText("Garmin connected")).toBeInTheDocument();
  });

  it("renders recovery score", () => {
    renderAthleteDetail();
    expect(screen.getByText("78")).toBeInTheDocument();
  });

  it("renders ACWR value", () => {
    renderAthleteDetail();
    expect(screen.getByText("1.07")).toBeInTheDocument();
  });

  it("renders HRV metric", () => {
    renderAthleteDetail();
    expect(screen.getByText("55.2")).toBeInTheDocument();
  });

  it("renders chart sections", () => {
    renderAthleteDetail();
    expect(screen.getByText("ACWR (28-day)")).toBeInTheDocument();
    expect(screen.getByText("HRV Trend (30-day)")).toBeInTheDocument();
    expect(screen.getByText("Sleep (14-day)")).toBeInTheDocument();
    expect(screen.getByText("Recovery Score (14-day)")).toBeInTheDocument();
  });

  it("renders anomalies section", () => {
    renderAthleteDetail();
    expect(screen.getByText("Active Anomalies (1)")).toBeInTheDocument();
    expect(screen.getByText("HRV below baseline")).toBeInTheDocument();
  });

  it("renders wellness table", () => {
    renderAthleteDetail();
    expect(screen.getByText("Recent Wellness")).toBeInTheDocument();
    expect(screen.getByText("450")).toBeInTheDocument();
  });
});
