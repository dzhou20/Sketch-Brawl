import qs from 'qs';

type LobbyResponse = { id: string; invite_code: string; status: string };
type HealthResponse = { status: string; version: string; env: string };

type DoodlePayload = {
  lobby_id: string;
  doodle_type: 'monster' | 'skill' | 'reinforcement';
  strokes: Array<{ x: number; y: number; pressure?: number; timestamp: number }>;
  metadata?: Record<string, unknown>;
  snapshot?: string;
};

export type InferenceResult = {
  ticket_id: string;
  payload: Record<string, unknown> | null;
  ready: boolean;
  waiting_for: string | null;
};

export type BattleEvent = {
  round: number;
  turn: number;
  attacker: string;
  defender: string;
  damage: number;
  defender_hp: number;
  event: string;
};

export type RoundSummary = {
  round: number;
  winner_slot: string;
  turns: number;
  ko_turn?: number | null;
  total_damage: Record<string, number>;
  hp_remaining: Record<string, number>;
};

export type CombatantPayload = {
  slot: string;
  name: string;
  element: string;
  base_hp: number;
  base_attack: number;
  skill_power: number;
  defence?: number;
  snapshot?: string | null;
  skills: Array<Record<string, any>>;
};

export type BattleResponse = {
  battle_id: number;
  winner_slot: string;
  wins: Record<string, number>;
  timeline: BattleEvent[];
  rounds: RoundSummary[];
  combatants: CombatantPayload[];
};

export type BattleJobStatus = {
  job_id: string;
  status: 'queued' | 'started' | 'failed' | 'finished';
  battle_id?: number | null;
  detail?: string | null;
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

  async getInference(ticketId: string): Promise<InferenceResult> {
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

  async startBattle(payload: { lobby_id: string; seed?: number }): Promise<BattleResponse> {
    const res = await fetch(`/api/proxy/battles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('battle start failed');
    return res.json();
  },

  async getBattle(battleId: number): Promise<BattleResponse> {
    const res = await fetch(`/api/proxy/battles/${battleId}`);
    if (!res.ok) throw new Error('battle fetch failed');
    return res.json();
  },

  async startBattleAsync(payload: { lobby_id: string; seed?: number }): Promise<{ job_id: string }> {
    const res = await fetch(`/api/proxy/battles/async`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('battle queue failed');
    return res.json();
  },

  async getBattleJob(jobId: string): Promise<BattleJobStatus> {
    const res = await fetch(`/api/proxy/battles/jobs/${jobId}`);
    if (!res.ok) throw new Error('battle job fetch failed');
    return res.json();
  },

  subscribeBattleStream(battleId: number, onEvent: (event: BattleEvent) => void): () => void {
    const source = new EventSource(`/api/proxy/battles/${battleId}/events`);
    source.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        onEvent(payload as BattleEvent);
      } catch (_err) {
        // ignore malformed events
      }
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  },
};
