import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthletes: () => ({
    data: [
      { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
    ],
  }),
}));

vi.mock("@/api/hooks/useSessions", () => ({
  useAthleteSessions: () => ({
    data: [
      { id: "s1", athlete_id: "a1", source: "garmin", session_type: "running", start_time: "2026-02-27T07:00:00Z", duration_minutes: 45 },
      { id: "s2", athlete_id: "a1", source: "manual", session_type: "strength", start_time: "2026-02-26T16:00:00Z", duration_minutes: 60 },
    ],
    isLoading: false,
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

import { SessionListPage } from "@/features/sessions/SessionListPage";

describe("SessionListPage", () => {
  it("renders page title", () => {
    renderWithProviders(<SessionListPage />);
    expect(screen.getByText("Sessions")).toBeInTheDocument();
  });

  it("renders session rows", () => {
    renderWithProviders(<SessionListPage />);
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("strength")).toBeInTheDocument();
  });

  it("displays duration", () => {
    renderWithProviders(<SessionListPage />);
    expect(screen.getByText("45 min")).toBeInTheDocument();
    expect(screen.getByText("60 min")).toBeInTheDocument();
  });

  it("displays source", () => {
    renderWithProviders(<SessionListPage />);
    expect(screen.getByText("garmin")).toBeInTheDocument();
    expect(screen.getByText("manual")).toBeInTheDocument();
  });

  it("renders filter dropdowns", () => {
    renderWithProviders(<SessionListPage />);
    expect(screen.getByLabelText("Select athlete")).toBeInTheDocument();
    expect(screen.getByLabelText("Session type")).toBeInTheDocument();
    expect(screen.getByLabelText("Source")).toBeInTheDocument();
  });
});
