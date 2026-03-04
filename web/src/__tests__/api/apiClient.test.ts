import { describe, it, expect, vi, beforeEach } from "vitest";

// We need to test the module behavior, so we re-import after resetting
let apiClient: typeof import("@/api/client").apiClient;
let setTokens: typeof import("@/api/client").setTokens;
let clearTokens: typeof import("@/api/client").clearTokens;
let getAccessToken: typeof import("@/api/client").getAccessToken;

describe("API Client", () => {
  beforeEach(async () => {
    vi.resetModules();
    const mod = await import("@/api/client");
    apiClient = mod.apiClient;
    setTokens = mod.setTokens;
    clearTokens = mod.clearTokens;
    getAccessToken = mod.getAccessToken;
  });

  it("creates axios instance with correct base URL", () => {
    expect(apiClient.defaults.baseURL).toBe("http://localhost:8001");
  });

  it("sets and clears tokens", () => {
    setTokens("access-123", "refresh-456");
    expect(getAccessToken()).toBe("access-123");

    clearTokens();
    expect(getAccessToken()).toBeNull();
  });

  it("request interceptor adds auth header when token exists", async () => {
    setTokens("my-token", "refresh-token");

    // Test that the interceptor modifies the config
    const interceptors = apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (config: Record<string, unknown>) => Record<string, unknown> }>;
    };
    const handler = interceptors.handlers[0];
    expect(handler).toBeDefined();

    const config = { headers: {} as Record<string, string> };
    const result = handler!.fulfilled(config) as { headers: { Authorization: string } };
    expect(result.headers.Authorization).toBe("Bearer my-token");
  });

  it("request interceptor does not add auth header when no token", async () => {
    clearTokens();

    const interceptors = apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (config: Record<string, unknown>) => Record<string, unknown> }>;
    };
    const handler = interceptors.handlers[0];
    const config = { headers: {} as Record<string, string> };
    const result = handler!.fulfilled(config) as { headers: Record<string, string> };
    expect(result.headers["Authorization"]).toBeUndefined();
  });
});
