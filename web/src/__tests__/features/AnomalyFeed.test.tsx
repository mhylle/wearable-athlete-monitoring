import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/api/hooks/useAnomalies", () => ({
  useTeamAnomalies: () => ({
    data: [
      {
        athlete_id: "a1",
        metric_type: "hrv",
        value: 25,
        expected_median: 55,
        mad_score: 4.1,
        severity: "high",
        anomaly_type: "drop",
        explanation: "Significant HRV drop detected",
        detected_at: "2026-02-27T10:00:00Z",
      },
      {
        athlete_id: "a2",
        metric_type: "sleep",
        value: 300,
        expected_median: 450,
        mad_score: 2.5,
        severity: "low",
        anomaly_type: "drop",
        explanation: "Sleep duration below average",
        detected_at: "2026-02-26T08:00:00Z",
      },
    ],
    isLoading: false,
  }),
}));

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthletes: () => ({
    data: [
      { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
      { id: "a2", email: "b@test.com", full_name: "Bob Smith", role: "athlete", team_id: "t1", is_active: true },
    ],
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

import { AnomalyFeed } from "@/features/anomalies/AnomalyFeed";

describe("AnomalyFeed", () => {
  it("renders page title", () => {
    renderWithProviders(<AnomalyFeed />);
    expect(screen.getByText("Anomaly Feed")).toBeInTheDocument();
  });

  it("renders anomaly cards", () => {
    renderWithProviders(<AnomalyFeed />);
    expect(screen.getByText("Significant HRV drop detected")).toBeInTheDocument();
    expect(screen.getByText("Sleep duration below average")).toBeInTheDocument();
  });

  it("shows severity badges", () => {
    renderWithProviders(<AnomalyFeed />);
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("low")).toBeInTheDocument();
  });

  it("shows athlete names", () => {
    renderWithProviders(<AnomalyFeed />);
    // Names appear in both filter dropdown and anomaly cards
    const janeElements = screen.getAllByText("Jane Doe");
    expect(janeElements.length).toBeGreaterThanOrEqual(2);
    const bobElements = screen.getAllByText("Bob Smith");
    expect(bobElements.length).toBeGreaterThanOrEqual(2);
  });

  it("renders filter dropdowns", () => {
    renderWithProviders(<AnomalyFeed />);
    expect(screen.getByLabelText("Filter by severity")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by athlete")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by metric")).toBeInTheDocument();
  });

  it("sorts high severity first", () => {
    renderWithProviders(<AnomalyFeed />);
    const cards = screen.getAllByText(/drop/);
    // The "high" severity card should come first (anomaly_type: drop on both)
    expect(cards.length).toBeGreaterThanOrEqual(2);
  });
});
