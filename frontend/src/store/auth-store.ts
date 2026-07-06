import { create } from "zustand";

interface UserState {
  email: string;
  role: string;
}

interface AuthStore {
  token: string | null;
  user: UserState | null;
  isAuthenticated: boolean;
  login: (token: string, user: UserState) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => {
  // Safe extraction for SSR
  const initialToken = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const initialUser = typeof window !== "undefined" ? localStorage.getItem("auth_user") : null;

  return {
    token: initialToken,
    user: initialUser ? JSON.parse(initialUser) : null,
    isAuthenticated: !!initialToken,
    login: (token, user) => {
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", token);
        localStorage.setItem("auth_user", JSON.stringify(user));
      }
      set({ token, user, isAuthenticated: true });
    },
    logout: () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
      }
      set({ token: null, user: null, isAuthenticated: false });
    },
  };
});
