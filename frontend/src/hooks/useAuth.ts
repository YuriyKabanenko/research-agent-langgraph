import { useMutation } from "@tanstack/react-query";
import * as authApi from "../api/auth";
import { authStore, useAuthStore } from "../store/authStore";
import type { LoginRequest, RegisterRequest } from "../api/types";

export function useAuthToken() {
  return useAuthStore((s) => s.token);
}

export function useRegister() {
  return useMutation({
    mutationFn: (body: RegisterRequest) => authApi.register(body),
    onSuccess: (data) => authStore.getState().setToken(data.token),
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: (body: LoginRequest) => authApi.login(body),
    onSuccess: (data) => authStore.getState().setToken(data.token),
  });
}

export function useLogout() {
  return () => authStore.getState().logout();
}
