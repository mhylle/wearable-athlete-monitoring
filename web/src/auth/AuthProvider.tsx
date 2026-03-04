import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import { apiClient, setTokens, clearTokens, setOnAuthFailure } from "@/api/client";
import type { AuthContextValue, User } from "./types";

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!accessToken;

  const logout = useCallback(() => {
    clearTokens();
    setAccessToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setOnAuthFailure(logout);
  }, [logout]);

  const fetchUser = useCallback(async () => {
    try {
      const response = await apiClient.get<User>("/api/v1/auth/me");
      setUser(response.data);
    } catch {
      logout();
    }
  }, [logout]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await apiClient.post("/api/v1/auth/login", {
        email,
        password,
      });

      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      setAccessToken(access_token);

      await fetchUser();
    },
    [fetchUser]
  );

  useEffect(() => {
    // On mount, we have no stored tokens (in-memory only), so just mark loading done
    setIsLoading(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, accessToken, isAuthenticated, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
