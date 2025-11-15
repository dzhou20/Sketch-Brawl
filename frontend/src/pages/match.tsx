'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { apiClient, type BattleEvent, type BattleResponse } from '@/services/apiClient';
import { DoodleCanvas } from '@/components/DoodleCanvas';
import { AttributionPanel } from '@/components/AttributionPanel';
import { BattleHud } from '@/components/BattleHud';
import { SkillCardPanel } from '@/components/SkillCardPanel';

const doodleOptions = ['monster', 'skill', 'reinforcement'] as const;

export default function MatchPage() {
  const { lobbyId, ensureLobby, playerSlot, switchPlayer } = useSessionStore();
  const [status, setStatus] = useState('bootstrapping');
  const [doodleType, setDoodleType] = useState<(typeof doodleOptions)[number]>('monster');
  const [activePayload, setActivePayload] = useState<Record<string, any> | null>(null);
  const [latestMonsters, setLatestMonsters] = useState<Record<'A' | 'B', Record<string, any> | null>>({
    A: null,
    B: null,
  });
  const [latestSkills, setLatestSkills] = useState<Record<'A' | 'B', Record<string, any> | null>>({
    A: null,
    B: null,
  });
  const [battleResult, setBattleResult] = useState<BattleResponse | null>(null);
  const [liveEvents, setLiveEvents] = useState<BattleEvent[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      setStatus('joining');
      await ensureLobby();
      setStatus('ready');
    }
    bootstrap();
  }, [ensureLobby]);

  useEffect(() => {
    if (doodleType === 'monster') {
      setActivePayload(latestMonsters[playerSlot]);
    } else if (doodleType === 'skill') {
      setActivePayload(latestSkills[playerSlot]);
    } else {
      setActivePayload(null);
    }
  }, [doodleType, playerSlot, latestMonsters, latestSkills]);

  const metadataOverrides = useMemo<Record<string, unknown>>(() => {
    const overrides: Record<string, unknown> = {};
    const monster = latestMonsters[playerSlot];
    const skill = latestSkills[playerSlot];
    if (monster?.monster_id) {
      overrides.monster_id = monster.monster_id;
    }
    if (doodleType === 'reinforcement' && skill?.skill_id) {
      overrides.skill_id = skill.skill_id;
    }
    return overrides;
  }, [doodleType, playerSlot, latestMonsters, latestSkills]);

  const handleInferenceResult = (result: Record<string, any>) => {
    if (doodleType === 'monster') {
      setLatestMonsters((prev) => ({ ...prev, [playerSlot]: result }));
    } else if (doodleType === 'skill' || doodleType === 'reinforcement') {
      setLatestSkills((prev) => {
        const existing = prev[playerSlot] ?? {};
        return { ...prev, [playerSlot]: { ...existing, ...result } };
      });
    }
    setActivePayload(result);
  };

  useEffect(() => {
    if (!jobId) return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const status = await apiClient.getBattleJob(jobId);
        if (cancelled) return;
        if (status.status === 'finished' && status.battle_id) {
          const battle = await apiClient.getBattle(status.battle_id);
          setBattleResult(battle);
          startStream(battle.battle_id);
          setJobId(null);
          setStatus('ready');
        } else if (status.status === 'failed') {
          setError(status.detail ?? 'Battle job failed');
          setJobId(null);
          setStatus('ready');
        } else {
          setTimeout(poll, 900);
        }
      } catch (err) {
        setError((err as Error).message);
        setJobId(null);
        setStatus('ready');
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const startStream = (battleId: number) => {
    setLiveEvents([]);
    apiClient.subscribeBattleStream(battleId, (event) => {
      setLiveEvents((prev) => [...prev, event]);
    });
  };

  return (
    <div className="match-layout">
      <header>
        <h1>Sketch Brawl Lobby {lobbyId ?? '...'}</h1>
        <p>Status: {status}</p>
        <button onClick={() => apiClient.health()}>API Health</button>
        <button onClick={switchPlayer}>Switch Player ({playerSlot})</button>
        <button
          onClick={async () => {
            if (!lobbyId) return;
            try {
              setError(null);
              setStatus('battling');
              const battle = await apiClient.startBattle({ lobby_id: lobbyId });
              setBattleResult(battle);
               startStream(battle.battle_id);
              setStatus('ready');
            } catch (err) {
              console.error(err);
              setError((err as Error).message);
              setStatus('ready');
            }
          }}
        >
          Start Battle
        </button>
        <button
          onClick={async () => {
            if (!lobbyId) return;
            try {
              setError(null);
              setStatus('queueing');
              const ticket = await apiClient.startBattleAsync({ lobby_id: lobbyId });
              setJobId(ticket.job_id);
            } catch (err) {
              console.error(err);
              setError((err as Error).message);
              setStatus('ready');
            }
          }}
        >
          Queue Async Battle
        </button>
      </header>
      <div className="toolbar">
        {doodleOptions.map((option) => (
          <button
            key={option}
            className={option === doodleType ? 'active' : ''}
            onClick={() => setDoodleType(option)}
          >
            {option}
          </button>
        ))}
      </div>
      <div className="workbench">
        <DoodleCanvas
          lobbyId={lobbyId}
          playerSlot={playerSlot}
          doodleType={doodleType}
          onResult={handleInferenceResult}
          metadataOverrides={metadataOverrides}
        />
        <AttributionPanel payload={activePayload} doodleType={doodleType} />
        <SkillCardPanel
          slot={playerSlot}
          skill={latestSkills[playerSlot]}
          onReinforce={() => setDoodleType('reinforcement')}
        />
        <BattleHud battle={battleResult} liveEvents={liveEvents} />
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
