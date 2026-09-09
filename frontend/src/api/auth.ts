import { apiFetch } from "./client";
import type { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse } from "./types";

export function register(body: RegisterRequest): Promise<RegisterResponse> {
  return apiFetch<RegisterResponse>("/register", { method: "POST", body });
}

export function login(body: LoginRequest): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/login", { method: "POST", body });
}
