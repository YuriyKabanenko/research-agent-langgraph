import { authStore } from "../store/authStore";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

interface ApiFetchOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const token = authStore.getState().token;

  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    if (response.status === 401) {
      authStore.getState().logout();
    }
    const body = await response.json().catch(() => null);
    const detail =
      (body && typeof body.detail === "string" && body.detail) || response.statusText;
    throw new ApiError(response.status, detail);
  }

  // 202/204 responses with no body would break response.json() - only parse when
  // there's actually content to parse.
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
