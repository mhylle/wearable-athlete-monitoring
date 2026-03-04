import { render, screen, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AuthProvider, useAuth } from "@/auth/AuthProvider";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  setOnAuthFailure: vi.fn(),
}));

import { apiClient } from "@/api/client";

function AuthConsumer() {
  const { isAuthenticated, user, login } = useAuth();
  return (
    <div>
      <span data-testid="auth-status">
        {isAuthenticated ? "authenticated" : "unauthenticated"}
      </span>
      <span data-testid="user-name">{user?.full_name ?? "none"}</span>
      <button
        onClick={() => login("test@example.com", "password123")}
        data-testid="login-btn"
      >
        Login
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("provides auth context to children", () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );
    expect(screen.getByTestId("auth-status")).toBeInTheDocument();
  });

  it("is unauthenticated initially", () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );
    expect(screen.getByTestId("auth-status")).toHaveTextContent("unauthenticated");
    expect(screen.getByTestId("user-name")).toHaveTextContent("none");
  });

  it("sets authenticated state and user after login", async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        access_token: "test-access-token",
        refresh_token: "test-refresh-token",
        token_type: "bearer",
      },
    });
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        id: "user-1",
        email: "test@example.com",
        role: "coach",
        full_name: "Test Coach",
        team_id: null,
      },
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByTestId("login-btn").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated");
      expect(screen.getByTestId("user-name")).toHaveTextContent("Test Coach");
    });
  });
});
