import { create } from "zustand";

interface AppState {
  isLoggedIn: boolean;
  trainerName: string;
  login: (name: string) => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  isLoggedIn: false,
  trainerName: "",
  login: (name: string) => set({ isLoggedIn: true, trainerName: name }),
  logout: () => set({ isLoggedIn: false, trainerName: "" }),
}));
