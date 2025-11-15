'use client';

import Head from 'next/head';
import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { apiClient, type BattleEvent, type BattleResponse } from '@/services/apiClient';
import { DoodleCanvas } from '@/components/DoodleCanvas';
import { AttributionPanel } from '@/components/AttributionPanel';
import { BattleHud } from '@/components/BattleHud';
import { SkillCardPanel } from '@/components/SkillCardPanel';
import { BattleStage, type StageFighter } from '@/components/BattleStage';

const doodleOptions = ['monster', 'skill', 'reinforcement'] as const;
const matchTexture = 'https://www.figma.com/api/mcp/asset/dd8c5d58-1c22-4e26-8d1d-d9e0e43ec803';
const thinkingTexture = 'https://www.figma.com/api/mcp/asset/7f42557b-8907-4c36-ac8b-f61b9e016ba0';
const thinkingVector = 'https://www.figma.com/api/mcp/asset/aa3914c2-f0e7-489d-af85-32edc78f6f67';
type CSSVarStyle = CSSProperties & { [key: `--${string}`]: string };

const phaseCopy: Record<
  (typeof doodleOptions)[number],
  { title: string; subtitle: (slot: 'A' | 'B') => string }
> = {
  monster: {
    title: 'Draw Your Monster',
    subtitle: (slot) => `Player ${slot}, sketch your creature so the AI can reveal its power.`,
  },
  skill: {
    title: 'Draw Your Gear',
    subtitle: (slot) => `Player ${slot}, add a weapon or shield to define your fighting style.`,
  },
  reinforcement: {
    title: 'Upgrade Your Gear',
    subtitle: (slot) => `Player ${slot}, reinforce an existing skill to gain an edge next round.`,
  },
};

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
  const [thinkingPlayer, setThinkingPlayer] = useState<'A' | 'B' | null>(null);
  const [showSummary, setShowSummary] = useState(false);

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

  const stageFighters = useMemo<StageFighter[]>(() => {
    if (battleResult?.combatants?.length) {
      return battleResult.combatants.map((combatant) => ({
        slot: (combatant.slot === 'B' ? 'B' : 'A') as 'A' | 'B',
        name: combatant.name,
        element: combatant.element,
        snapshot: combatant.snapshot ?? null,
      }));
    }
    return (['A', 'B'] as const).reduce<StageFighter[]>((acc, slot) => {
      const monster = latestMonsters[slot];
      if (!monster) {
        return acc;
      }
      acc.push({
        slot,
        name: monster.name ?? `Player ${slot}`,
        element: monster.element ?? monster.primary_element ?? 'mystery',
        snapshot: monster.snapshot ?? monster.image ?? null,
      });
      return acc;
    }, []);
  }, [battleResult, latestMonsters]);

  const stageEvents = liveEvents.length > 0 ? liveEvents : battleResult?.timeline ?? [];

  const matchStyle: CSSVarStyle = {
    '--match-texture': `url(${matchTexture})`,
  };
  const aiOverlayStyle: CSSVarStyle = {
    '--thinking-texture': `url(${thinkingTexture})`,
  };
  const phaseTitle = phaseCopy[doodleType].title;
  const phaseSubtitle = phaseCopy[doodleType].subtitle(playerSlot);

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
    setThinkingPlayer(null);
  };

  const playerPanels = (['A', 'B'] as const).map((slot) => {
    const isActive = slot === playerSlot;
    const candidateSkill = latestSkills[slot];
    const latestSubmission =
      doodleType === 'monster' ? latestMonsters[slot] : candidateSkill ?? latestMonsters[slot];
    const preview =
      latestSubmission?.snapshot ??
      latestSubmission?.card_snapshot ??
      latestSubmission?.card_image ??
      latestSubmission?.image ??
      null;
    const label = slot === 'A' ? 'PLAYER 1' : 'PLAYER 2';
    const submitted = Boolean(preview);

    return (
      <article
        key={slot}
        className={`player-panel ${slot === 'A' ? 'player-panel--dashed' : 'player-panel--solid'} ${
          isActive ? 'player-panel--active' : ''
        }`}
        data-slot={slot}
      >
        <p className="player-panel-label">{label}</p>
        <div className="player-frame">
          {isActive ? (
            <DoodleCanvas
              lobbyId={lobbyId}
              playerSlot={playerSlot}
              doodleType={doodleType}
              onResult={handleInferenceResult}
              metadataOverrides={metadataOverrides}
              onSubmitStateChange={(state) => {
                if (state === 'submitting') {
                  setThinkingPlayer(playerSlot);
                } else {
                  setThinkingPlayer(null);
                }
              }}
              strokeColor="#111111"
              backgroundColor="#faf9f5"
              submitLabel="SUBMIT"
              clearLabel="CLEAR"
            />
          ) : preview ? (
            <img src={preview} alt={`${label} submission`} />
          ) : (
            <p className="player-placeholder">Waiting for sketch…</p>
          )}
        </div>
        <p className={`player-status ${submitted ? 'is-complete' : ''}`}>
          {isActive ? phaseSubtitle : submitted ? 'SUBMITTED' : 'WAITING'}
        </p>
      </article>
    );
  });

  const thinkingPreview = {
    A: latestMonsters.A?.snapshot ?? latestMonsters.A?.image ?? null,
    B: latestMonsters.B?.snapshot ?? latestMonsters.B?.image ?? null,
  };

  const aiStatusLabel = status === 'queueing' ? 'Queueing AI...' : 'AI THINKING...';

  const isThinking =
    thinkingPlayer !== null || jobId !== null || status === 'queueing' || status === 'battling';

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
          setShowSummary(true);
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
    <div className="match-screen" style={matchStyle}>
      <Head>
        <title>Sketch Brawl Match</title>
      </Head>
      <section className="match-hero" data-node-id="42:1961">
        <p className="eyebrow">
          {phaseTitle} · Player {playerSlot}
        </p>
        <h1 data-node-id="42:2003">{phaseTitle}</h1>
        <p className="subtitle">{phaseSubtitle}</p>
        <div className="player-grid" data-node-id="42:1965">
          {playerPanels[0]}
          <div className="match-arrow" aria-hidden>
            <svg viewBox="0 0 160 40" role="presentation">
              <path d="M10 20 H150" />
              <path d="M20 10 L10 20 L20 30" />
              <path d="M140 10 L150 20 L140 30" />
            </svg>
            <span>draw here</span>
          </div>
          {playerPanels[1]}
        </div>
        <div className="match-tools">
          <span className="match-tool match-tool--pencil" aria-label="pencil" />
          <span className="match-tool match-tool--eraser" aria-label="eraser" />
        </div>
      </section>

      <section className="match-admin">
        <div>
          <p className="eyebrow">Lobby</p>
          <h2>{lobbyId ?? 'Loading…'}</h2>
        </div>
        <div>
          <p className="eyebrow">Status</p>
          <p className="match-status">{status}</p>
        </div>
        <div className="match-admin-actions">
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
                setShowSummary(true);
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
        </div>
      </section>

      <div className="toolbar match-toolbar">
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

      <div className="workbench match-dashboard">
        <AttributionPanel payload={activePayload} doodleType={doodleType} />
        <SkillCardPanel
          slot={playerSlot}
          skill={latestSkills[playerSlot]}
          onReinforce={() => setDoodleType('reinforcement')}
        />
        <BattleStage fighters={stageFighters} events={stageEvents} />
        <BattleHud battle={battleResult} liveEvents={liveEvents} />
      </div>

      <StepIndicator
        title={phaseCopy[doodleType].title}
        subtitle={phaseCopy[doodleType].subtitle(playerSlot)}
      />
      {isThinking && (
        <AiThinkingOverlay
          style={aiOverlayStyle}
          leftPreview={thinkingPreview.A}
          rightPreview={thinkingPreview.B}
          statusLabel={aiStatusLabel}
        />
      )}
      {battleResult && showSummary && (
        <BattleSummaryModal
          battle={battleResult}
          onUpgrade={() => {
            setDoodleType('reinforcement');
            setShowSummary(false);
            setBattleResult(battleResult);
          }}
          onClose={() => setShowSummary(false)}
        />
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}

function StepIndicator({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <section className="step-indicator">
      <div>
        <p className="eyebrow">current step</p>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
    </section>
  );
}

type AiThinkingOverlayProps = {
  style?: CSSVarStyle;
  leftPreview?: string | null;
  rightPreview?: string | null;
  statusLabel: string;
};

function AiThinkingOverlay({ style, leftPreview, rightPreview, statusLabel }: AiThinkingOverlayProps) {
  const panels = [
    { slot: 'A' as const, label: 'PLAYER 1', preview: leftPreview, nodeId: '42:2274' },
    { slot: 'B' as const, label: 'PLAYER 2', preview: rightPreview, nodeId: '42:2277' },
  ];

  return (
    <div className="ai-thinking-overlay" style={style}>
      <div className="ai-thinking-wrapper">
        <p className="ai-thinking-title" data-node-id="42:2275">
          Draw Your Monster!
        </p>
        <div className="ai-thinking-panels">
          {panels.map((panel) => (
            <article
              key={panel.slot}
              className={`player-panel ai-thinking-panel ${
                panel.slot === 'A' ? 'player-panel--dashed' : 'player-panel--solid'
              }`}
              data-slot={panel.slot}
            >
              <p className="player-panel-label" data-node-id={panel.nodeId}>
                {panel.label}
              </p>
              <div className="player-frame">
                {panel.preview ? (
                  <img src={panel.preview} alt={`${panel.label} preview`} />
                ) : (
                  <p className="player-placeholder">Waiting for sketch…</p>
                )}
              </div>
            </article>
          ))}
          <div className="ai-thinking-vector" data-node-id="42:2278">
            <img src={thinkingVector} alt="" aria-hidden />
          </div>
        </div>
        <p className="ai-thinking-status" data-node-id="42:2276">
          {statusLabel}
        </p>
      </div>
    </div>
  );
}

function BattleSummaryModal({
  battle,
  onUpgrade,
  onClose,
}: {
  battle: BattleResponse;
  onUpgrade: () => void;
  onClose: () => void;
}) {
  const winner = battle.winner_slot;
  return (
    <div className="summary-backdrop">
      <div className="summary-modal">
        <p className="eyebrow">battle complete</p>
        <h2>Player {winner} wins!</h2>
        <p>
          Ready for the next round? Reinforce your gear or head back to the lobby to start over. The
          judges can review the recap log for every hit.
        </p>
        <div className="summary-actions">
          <button onClick={onUpgrade}>Upgrade Gear</button>
          <button className="secondary" onClick={onClose}>
            Back to main menu
          </button>
        </div>
      </div>
    </div>
  );
}
