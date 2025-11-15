import { create } from 'zustand';
import { apiClient } from '@/services/apiClient';

interface SessionState {
  lobbyId: string | null;
  ensureLobby: () => Promise<void>;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  lobbyId: null,
  ensureLobby: async () => {
    if (get().lobbyId) return;
    const lobby = await apiClient.createLobby();
    set({ lobbyId: lobby.id });
  },
}));
