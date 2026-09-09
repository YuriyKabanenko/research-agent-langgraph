import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
}

// A plain store, not a React hook wrapper: usable both as a hook (`useAuthStore(s =>
// s.token)`, inside components) and via `authStore.getState()` (outside components,
// e.g. in api/client.ts, which isn't allowed to call hooks). `persist` backs it with
// localStorage under the key below - nothing else in the app should read/write that
// key directly, or the two would drift out of sync.
export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      setToken: (token) => set({ token }),
      logout: () => set({ token: null }),
    }),
    { name: "auth" },
  ),
);

// Re-exported under the conventional hook name for use inside components.
export const useAuthStore = authStore;
