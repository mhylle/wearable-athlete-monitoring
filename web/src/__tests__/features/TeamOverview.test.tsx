import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthletes: () => ({
    data: [
      { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
      { id: "a2", email: "b@test.com", full_name: "Bob Smith", role: "athlete", team_id: "t1", is_active: true },
    ],
    isLoading: false,
  }),
}));

vi.mock("@/api/hooks/useAnalytics", () => ({
  useTeamACWROverview: () => ({
    data: [
      { athlete_id: "a1", athlete_name: "Jane Doe", acwr_value: 1.1, zone: "optimal" },
      { athlete_id: "a2", athlete_name: "Bob Smith", acwr_value: 1.6, zone: "high_risk" },
    ],
  }),
  useTeamRecoveryOverview: () => ({
    data: [
      { athlete_id: "a1", athlete_name: "Jane Doe", total_score: 82 },
      { athlete_id: "a2", athlete_name: "Bob Smith", total_score: 45 },
    ],
  }),
}));

vi.mock("@/api/hooks/useAnomalies", () => ({
  useTeamAnomalies: () => ({
    data: [
      { athlete_id: "a2", metric_type: "hrv", value: 20, expected_median: 55, mad_score: 4.5, severity: "high", anomaly_type: "drop", explanation: "HRV dropped", detected_at: "2026-02-27T10:00:00Z" },
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

import { TeamOverviewPage } from "@/features/team/TeamOverviewPage";

describe("TeamOverviewPage", () => {
  it("renders athlete cards", () => {
    renderWithProviders(<TeamOverviewPage />);
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();
  });

  it("displays recovery scores", () => {
    renderWithProviders(<TeamOverviewPage />);
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument();
  });

  it("shows ACWR zone badges", () => {
    renderWithProviders(<TeamOverviewPage />);
    // "Optimal" and "High Risk" appear both in badges and filter options, use getAllByText
    const optimalElements = screen.getAllByText("Optimal");
    expect(optimalElements.length).toBeGreaterThanOrEqual(2); // badge + option
    const highRiskElements = screen.getAllByText("High Risk");
    expect(highRiskElements.length).toBeGreaterThanOrEqual(2); // badge + option
  });

  it("shows anomaly count", () => {
    renderWithProviders(<TeamOverviewPage />);
    expect(screen.getByText("1 anomaly")).toBeInTheDocument();
  });

  it("renders the page title", () => {
    renderWithProviders(<TeamOverviewPage />);
    expect(screen.getByText("Team Overview")).toBeInTheDocument();
  });
});
