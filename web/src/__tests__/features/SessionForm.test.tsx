import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockMutate = vi.fn();

vi.mock("@/api/hooks/useAthletes", () => ({
  useAthletes: () => ({
    data: [
      { id: "a1", email: "j@test.com", full_name: "Jane Doe", role: "athlete", team_id: "t1", is_active: true },
      { id: "a2", email: "b@test.com", full_name: "Bob Smith", role: "athlete", team_id: "t1", is_active: true },
    ],
  }),
}));

vi.mock("@/api/hooks/useSessions", () => ({
  useCreateSession: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

import { SessionCreateForm } from "@/features/sessions/SessionCreateForm";

function renderForm() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SessionCreateForm />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe("SessionCreateForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the form title", () => {
    renderForm();
    expect(screen.getByRole("heading", { name: "Log Session" })).toBeInTheDocument();
  });

  it("renders athlete selector with athletes", () => {
    renderForm();
    expect(screen.getByLabelText("Athlete")).toBeInTheDocument();
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("Bob Smith")).toBeInTheDocument();
  });

  it("renders session type selector", () => {
    renderForm();
    expect(screen.getByLabelText("Session Type")).toBeInTheDocument();
    expect(screen.getByText("Match")).toBeInTheDocument();
    expect(screen.getByText("Training")).toBeInTheDocument();
    expect(screen.getByText("Gym")).toBeInTheDocument();
    expect(screen.getByText("Recovery")).toBeInTheDocument();
  });

  it("renders date and time inputs", () => {
    renderForm();
    expect(screen.getByLabelText("Start Date")).toBeInTheDocument();
    expect(screen.getByLabelText("Start Time")).toBeInTheDocument();
    expect(screen.getByLabelText("End Date")).toBeInTheDocument();
    expect(screen.getByLabelText("End Time")).toBeInTheDocument();
  });

  it("renders optional metric fields", () => {
    renderForm();
    expect(screen.getByLabelText("Distance (m)")).toBeInTheDocument();
    expect(screen.getByLabelText("Avg HR")).toBeInTheDocument();
    expect(screen.getByLabelText("Max HR")).toBeInTheDocument();
  });

  it("renders notes textarea", () => {
    renderForm();
    expect(screen.getByLabelText("Notes")).toBeInTheDocument();
  });

  it("shows validation error when submitting without athlete", async () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /log session/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Please select an athlete.");
    });
  });

  it("shows validation error when submitting without session type", async () => {
    renderForm();
    fireEvent.change(screen.getByLabelText("Athlete"), { target: { value: "a1" } });
    fireEvent.click(screen.getByRole("button", { name: /log session/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Please select a session type.");
    });
  });

  it("shows validation error when submitting without start date/time", async () => {
    renderForm();
    fireEvent.change(screen.getByLabelText("Athlete"), { target: { value: "a1" } });
    fireEvent.change(screen.getByLabelText("Session Type"), { target: { value: "training" } });
    fireEvent.click(screen.getByRole("button", { name: /log session/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Please enter a start date and time.");
    });
  });

  it("calls mutate on valid form submit with manual duration", async () => {
    renderForm();
    fireEvent.change(screen.getByLabelText("Athlete"), { target: { value: "a1" } });
    fireEvent.change(screen.getByLabelText("Session Type"), { target: { value: "training" } });
    fireEvent.change(screen.getByLabelText("Start Date"), { target: { value: "2026-02-28" } });
    fireEvent.change(screen.getByLabelText("Start Time"), { target: { value: "09:00" } });
    fireEvent.change(screen.getByLabelText(/duration/i), { target: { value: "60" } });
    fireEvent.click(screen.getByRole("button", { name: /log session/i }));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledTimes(1);
    });

    const callArgs = mockMutate.mock.calls[0]![0] as Record<string, unknown>;
    expect(callArgs.athlete_id).toBe("a1");
    expect(callArgs.session_type).toBe("training");
    expect(callArgs.duration_minutes).toBe(60);
    expect(callArgs.source).toBe("manual");
  });

  it("renders cancel and submit buttons", () => {
    renderForm();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log session/i })).toBeInTheDocument();
  });
});
