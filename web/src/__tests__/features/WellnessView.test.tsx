import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// --- WellnessOverviewPage tests ---

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthletes: () => ({
    data: [
      { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
      { id: "a2", email: "b@test.com", full_name: "Bob Smith", role: "athlete", team_id: "t1", is_active: true },
    ],
    isLoading: false,
  }),
  useAthlete: () => ({
    data: { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
  }),
}));

vi.mock("@/api/hooks/useWellness", () => ({
  useTeamWellnessOverview: () => ({
    data: [
      {
        athlete_id: "a1",
        athlete_name: "Jane Doe",
        submitted: true,
        latest_entry: { id: "w1", athlete_id: "a1", date: "2026-02-28", srpe: 400, soreness: 3, fatigue: 4, mood: 7, sleep_quality: 8 },
      },
      {
        athlete_id: "a2",
        athlete_name: "Bob Smith",
        submitted: false,
        latest_entry: null,
      },
    ],
  }),
  useAthleteWellness: () => ({
    data: [
      { id: "w1", athlete_id: "a1", date: "2026-02-28", srpe: 400, soreness: 3, fatigue: 4, mood: 7, sleep_quality: 8 },
      { id: "w2", athlete_id: "a1", date: "2026-02-27", srpe: 350, soreness: 2, fatigue: 3, mood: 8, sleep_quality: 7 },
    ],
    isLoading: false,
  }),
}));

vi.mock("recharts", () => {
  const MockChart = ({ children }: { children?: React.ReactNode }) => <div data-testid="mock-chart">{children}</div>;
  return {
    LineChart: MockChart,
    Line: () => null,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  };
});

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

import { WellnessOverviewPage } from "@/features/wellness/WellnessOverviewPage";
import { AthleteWellnessDetail } from "@/features/wellness/AthleteWellnessDetail";

describe("WellnessOverviewPage", () => {
  it("renders page title", () => {
    renderWithProviders(<WellnessOverviewPage />);
    expect(screen.getByText("Wellness Overview")).toBeInTheDocument();
  });

  it("renders athlete names in table", () => {
    renderWithProviders(<WellnessOverviewPage />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();
  });

  it("shows submission status", () => {
    renderWithProviders(<WellnessOverviewPage />);
    expect(screen.getByText("Submitted")).toBeInTheDocument();
    expect(screen.getByText("Not submitted")).toBeInTheDocument();
  });

  it("shows latest wellness values for submitted athletes", () => {
    renderWithProviders(<WellnessOverviewPage />);
    expect(screen.getByText("400")).toBeInTheDocument(); // sRPE
    expect(screen.getByText("7")).toBeInTheDocument(); // mood
  });

  it("renders view detail links", () => {
    renderWithProviders(<WellnessOverviewPage />);
    const links = screen.getAllByText("View detail");
    expect(links).toHaveLength(2);
  });
});

describe("AthleteWellnessDetail", () => {
  function renderDetail() {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/wellness/a1"]}>
          <Routes>
            <Route path="/wellness/:athleteId" element={<AthleteWellnessDetail />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  it("renders athlete name", () => {
    renderDetail();
    expect(screen.getByText(/Jane Doe/)).toBeInTheDocument();
  });

  it("renders wellness history table", () => {
    renderDetail();
    expect(screen.getByText("Wellness History")).toBeInTheDocument();
    expect(screen.getByText("400")).toBeInTheDocument();
    expect(screen.getByText("350")).toBeInTheDocument();
  });

  it("renders trend chart sections", () => {
    renderDetail();
    expect(screen.getByText("Mood Trend")).toBeInTheDocument();
    expect(screen.getByText("Soreness Trend")).toBeInTheDocument();
    expect(screen.getByText("Fatigue Trend")).toBeInTheDocument();
    expect(screen.getByText("Sleep Quality Trend")).toBeInTheDocument();
    expect(screen.getByText("sRPE Trend")).toBeInTheDocument();
  });

  it("shows entry count", () => {
    renderDetail();
    expect(screen.getByText("2 wellness entries")).toBeInTheDocument();
  });
});
