import qs from 'qs';

type LobbyResponse = { id: string; invite_code: string; status: string };
type HealthResponse = { status: string; version: string; env: string };

type DoodlePayload = {
  lobby_id: string;
  doodle_type: 'monster' | 'skill' | 'reinforcement';
  strokes: Array<{ x: number; y: number; pressure?: number; timestamp: number }>;
};

export const apiClient = {
  async health(): Promise<HealthResponse> {
    const res = await fetch(`/api/proxy/health`);
    if (!res.ok) throw new Error('health check failed');
    return res.json();
  },

  async createLobby(role: 'player' | 'judge' | 'spectator' = 'player'): Promise<LobbyResponse> {
    const res = await fetch(`/api/proxy/lobbies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invite_code: 'demo', role }),
    });
    if (!res.ok) throw new Error('unable to create lobby');
    return res.json();
  },

  async submitDoodle(payload: DoodlePayload) {
    const res = await fetch(`/api/proxy/doodles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('inference request failed');
    return res.json();
  },

  async getInference(ticketId: string) {
    const res = await fetch(`/api/proxy/doodles/${ticketId}`);
    if (!res.ok) throw new Error('inference fetch failed');
    return res.json();
  },

  async fetchTelemetry(params: { lobby_id?: string; battle_id?: string }) {
    const query = qs.stringify(params);
    const res = await fetch(`/api/proxy/telemetry?${query}`);
    if (!res.ok) throw new Error('telemetry fetch failed');
    return res.json();
  },

  async publishTelemetry(payload: { lobby_id: string; type: string; samples: number[] }) {
    await fetch(`/api/proxy/telemetry/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
};
