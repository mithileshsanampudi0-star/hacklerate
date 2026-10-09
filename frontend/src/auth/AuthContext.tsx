import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, refreshSession, tokens } from "../api/client";
import type { Me, Role } from "../api/types";

interface AuthState {
  user: Me | null;
  loading: boolean;
  login: (email: string, password: string, role: Role) => Promise<Me>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    tokens.clear();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    tokens.onAuthLost(logout);
    // Restore the session after a page reload using the stored refresh token.
    (async () => {
      if (tokens.hasRefresh() && (await refreshSession())) {
        try {
          setUser((await api.get<Me>("/auth/me")).data);
        } catch {
          tokens.clear();
        }
      }
      setLoading(false);
    })();
  }, [logout]);

  const login = useCallback(async (email: string, password: string, role: Role) => {
    const { data } = await api.post("/auth/login", { email, password, role });
    tokens.set(data.access_token, data.refresh_token);
    const me = (await api.get<Me>("/auth/me")).data;
    setUser(me);
    return me;
  }, []);

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
