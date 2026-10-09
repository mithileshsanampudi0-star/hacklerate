import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useQuery } from "@tanstack/react-query";

// Empty in dev (Vite proxies /api). On Vercel set VITE_API_URL to the Render URL.
const API_BASE = `${import.meta.env.VITE_API_URL ?? ""}/api`;
const REFRESH_KEY = "portal.refreshToken";

// The access token lives only in memory; the refresh token survives reloads.
let accessToken: string | null = null;
let onAuthLost: (() => void) | null = null;

function readRefresh(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export const tokens = {
  hasRefresh: () => readRefresh() !== null,
  set(access: string, refresh: string) {
    accessToken = access;
    try {
      localStorage.setItem(REFRESH_KEY, refresh);
    } catch {
      /* storage unavailable: session lasts until reload */
    }
  },
  clear() {
    accessToken = null;
    try {
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* ignore */
    }
  },
  onAuthLost(cb: () => void) {
    onAuthLost = cb;
  },
};

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

let refreshing: Promise<boolean> | null = null;

export function refreshSession(): Promise<boolean> {
  const refresh = readRefresh();
  if (!refresh) return Promise.resolve(false);
  refreshing ??= axios
    .post(`${API_BASE}/auth/refresh`, { refresh_token: refresh })
    .then((r) => {
      tokens.set(r.data.access_token, r.data.refresh_token);
      return true;
    })
    .catch(() => {
      tokens.clear();
      return false;
    })
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (error.response?.status === 401 && original && !original._retry && !original.url?.startsWith("/auth/")) {
      original._retry = true;
      if (await refreshSession()) return api(original);
      onAuthLost?.();
    }
    return Promise.reject(error);
  },
);

export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
    if (!err.response || err.response.status >= 500) {
      return "Cannot connect to the backend API server. Please ensure the backend is running on port 8000.";
    }
  }
  return "Something went wrong. Please try again.";
}

/** GET helper: the URL doubles as the cache key. */
export function useApi<T>(url: string | null) {
  return useQuery<T>({
    queryKey: [url],
    queryFn: () => api.get<T>(url!).then((r) => r.data),
    enabled: url !== null,
  });
}
