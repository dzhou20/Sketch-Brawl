import { create } from 'zustand';
import { apiClient } from '@/services/apiClient';

interface SessionState {
  lobbyId: string | null;
  playerSlot: 'A' | 'B';
  ensureLobby: () => Promise<void>;
  switchPlayer: () => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  lobbyId: null,
  playerSlot: 'A',
  ensureLobby: async () => {
    if (get().lobbyId) return;
    const lobby = await apiClient.createLobby();
    set({ lobbyId: lobby.id });
  },
  switchPlayer: () => {
    set((state) => ({
      playerSlot: state.playerSlot === 'A' ? 'B' : 'A',
    }));
  },
}));
