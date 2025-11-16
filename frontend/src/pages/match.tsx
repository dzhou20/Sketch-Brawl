'use client';

import Head from 'next/head';
import { useEffect, useMemo, useState, useRef, type CSSProperties } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { apiClient, type BattleEvent, type BattleResponse } from '@/services/apiClient';
import { DoodleCanvas, type DoodleCanvasRef } from '@/components/DoodleCanvas';
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

const ELEMENTS = ['Wood', 'Metal', 'Fire', 'Water', 'Earth', 'Wind', 'Light', 'Dark'];
const MONSTER_NAMES = [
  'Weird Bunny',
  'Fluffy Dragon',
  'Spiky Creature',
  'Bouncy Monster',
  'Mysterious Beast',
  'Silly Critter',
];
const GEAR_NAMES = [
  'Flame Sword',
  'Moai Shield',
  'Thunder Axe',
  'Wind Staff',
  'Crystal Bow',
  'Shadow Dagger',
];
const GEAR_MOVES = [
  'Fire Slay!',
  'Moai Shield Bash!',
  'Thunder Strike!',
  'Wind Cut!',
  'Crystal Beam!',
  'Shadow Lunge!',
];

const randomFrom = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
const randomInt = (min: number, max: number) =>
  Math.floor(Math.random() * (max - min + 1)) + min;

const buildMockMonsterPayload = (slot: 'A' | 'B', snapshot: string) => {
  const primary = randomFrom(ELEMENTS);
  const secondary = randomFrom(ELEMENTS.filter((el) => el !== primary));
  return {
    slot,
    name: randomFrom(MONSTER_NAMES),
    element: primary,
    primary_element: primary,
    secondary_element: secondary,
    hp: randomInt(55, 95),
    attack: randomInt(12, 24),
    defence: randomInt(60, 110),
    snapshot,
  };
};

const buildMockSkillPayload = (snapshot: string) => {
  const element = randomFrom(ELEMENTS);
  return {
    name: randomFrom(GEAR_NAMES),
    element,
    attack_move: randomFrom(GEAR_MOVES),
    power: randomInt(12, 28),
    card_snapshot: snapshot,
    snapshot,
    type: 'attack',
  };
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
  const [toolMode, setToolMode] = useState<'pen' | 'eraser'>('pen');
  const [showBattleView, setShowBattleView] = useState(false);
  const canvasRefs = useRef<Record<'A' | 'B', DoodleCanvasRef | null>>({ A: null, B: null });

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

  const handleInferenceResult = (
    slot: 'A' | 'B',
    result: Record<string, any>,
    context?: { snapshot?: string | null; doodleType?: (typeof doodleOptions)[number] },
  ) => {
    const submittedType = context?.doodleType ?? doodleType;
    const snapshot = context?.snapshot ?? result.snapshot ?? null;

    if (submittedType === 'monster') {
      setLatestMonsters((prev) => ({
        ...prev,
        [slot]: {
          ...(prev[slot] ?? {}),
          ...result,
          snapshot: result.snapshot ?? snapshot ?? prev[slot]?.snapshot ?? null,
          image: result.image ?? snapshot ?? prev[slot]?.image ?? null,
        },
      }));
    } else if (submittedType === 'skill' || submittedType === 'reinforcement') {
      setLatestSkills((prev) => {
        const existing = prev[slot] ?? {};
        const combinedSnapshot =
          result.card_snapshot ??
          result.snapshot ??
          snapshot ??
          existing.card_snapshot ??
          existing.snapshot ??
          null;
        return {
          ...prev,
          [slot]: {
            ...existing,
            ...result,
            card_snapshot: combinedSnapshot,
            snapshot: combinedSnapshot,
          },
        };
      });
    }

    setActivePayload(result);
    setThinkingPlayer(null);

    const otherSlot: 'A' | 'B' = slot === 'A' ? 'B' : 'A';
    const needsOtherSubmission =
      submittedType === 'monster'
        ? !(latestMonsters[otherSlot]?.snapshot ?? latestMonsters[otherSlot]?.image)
        : submittedType === 'skill'
          ? !(latestSkills[otherSlot]?.card_snapshot ?? latestSkills[otherSlot]?.snapshot)
          : false;

    if (needsOtherSubmission) {
      switchPlayer();
    }
  };

  const handleLocalSubmission = (slot: 'A' | 'B') => {
    const ref = canvasRefs.current[slot];
    if (!ref) return;
    const snapshot = ref.getSnapshot?.();
    if (!snapshot) return;

    const submissionType =
      doodleType === 'monster' ? 'monster' : doodleType === 'skill' ? 'skill' : 'reinforcement';

    const payload =
      submissionType === 'monster'
        ? buildMockMonsterPayload(slot, snapshot)
        : buildMockSkillPayload(snapshot);

    handleInferenceResult(slot, payload, { snapshot, doodleType: submissionType });
    ref.clear();
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
    const frameClass = `player-panel ${slot === 'A' ? 'player-panel--dashed' : 'player-panel--solid'} ${
      isActive ? 'player-panel--active' : ''
    }`;

    return (
      <article key={slot} className={frameClass} data-slot={slot}>
        <p className="player-panel-label">{label}</p>
        <div className="player-frame">
          {isActive ? (
            <DoodleCanvas
              ref={(instance) => {
                canvasRefs.current[slot] = instance ?? null;
              }}
              lobbyId={lobbyId}
              playerSlot={playerSlot}
              doodleType={doodleType}
              onResult={(payload, ctx) => handleInferenceResult(slot, payload, ctx)}
              metadataOverrides={metadataOverrides}
              onSubmitStateChange={(state) => {
                if (state === 'submitting') {
                  setThinkingPlayer(playerSlot);
                } else {
                  setThinkingPlayer(null);
                }
              }}
              strokeColor="#111111"
              backgroundColor="#ffffff"
              toolMode={toolMode}
            />
          ) : preview ? (
            <img src={preview} alt={`${label} submission`} />
          ) : (
            <p className="player-placeholder">Waiting for sketch…</p>
          )}
        </div>
        {isActive ? (
          <>
            <div className="player-actions">
              <button
                type="button"
                onClick={() => handleLocalSubmission(slot)}
                className="doodle-action-button"
              >
                SUBMIT
              </button>
              <button
                type="button"
                onClick={() => {
                  const ref = canvasRefs.current[slot];
                  if (ref) {
                    ref.clear();
                  }
                }}
                className="doodle-action-button"
              >
                CLEAR
              </button>
            </div>
            <p className="player-hint">{phaseSubtitle}</p>
          </>
        ) : (
          <p className={`player-status ${submitted ? 'is-complete' : ''}`}>
            {submitted ? 'SUBMITTED' : 'WAITING'}
          </p>
        )}
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

  // Mock battle function for frontend testing
  const startMockBattle = () => {
    const monsterA = latestMonsters.A;
    const monsterB = latestMonsters.B;
    const skillA = latestSkills.A;
    const skillB = latestSkills.B;

    // Generate mock battle data
    const mockBattle: BattleResponse = {
      battle_id: Date.now(),
      winner_slot: Math.random() > 0.5 ? 'A' : 'B',
      wins: { A: 0, B: 0 },
      combatants: [
        {
          slot: 'A',
          name: monsterA?.name || 'Player A Monster',
          element: monsterA?.element || monsterA?.primary_element || 'Fire',
          base_hp: monsterA?.hp || 100,
          base_attack: monsterA?.attack || 20,
          skill_power: skillA?.power || 15,
          defence: monsterA?.defence || 50,
          snapshot: monsterA?.snapshot || monsterA?.image || null,
          skills: skillA ? [{ id: skillA.skill_id, name: skillA.name, type: skillA.type || 'attack', attack_bonus: skillA.power || 15 }] : [],
        },
        {
          slot: 'B',
          name: monsterB?.name || 'Player B Monster',
          element: monsterB?.element || monsterB?.primary_element || 'Water',
          base_hp: monsterB?.hp || 100,
          base_attack: monsterB?.attack || 20,
          skill_power: skillB?.power || 15,
          defence: monsterB?.defence || 50,
          snapshot: monsterB?.snapshot || monsterB?.image || null,
          skills: skillB ? [{ id: skillB.skill_id, name: skillB.name, type: skillB.type || 'attack', attack_bonus: skillB.power || 15 }] : [],
        },
      ],
      rounds: [],
      timeline: [],
    };

    // Generate battle timeline
    const timeline: BattleEvent[] = [];
    let hpA = mockBattle.combatants[0].base_hp;
    let hpB = mockBattle.combatants[1].base_hp;
    let round = 1;
    let turn = 1;

    while (hpA > 0 && hpB > 0 && turn < 20) {
      // Random attacker
      const attacker = Math.random() > 0.5 ? 'A' : 'B';
      const defender = attacker === 'A' ? 'B' : 'A';
      
      const attackerData = mockBattle.combatants.find(c => c.slot === attacker)!;
      const damage = Math.floor(Math.random() * 20) + attackerData.base_attack + attackerData.skill_power;
      
      if (defender === 'A') {
        hpA = Math.max(0, hpA - damage);
      } else {
        hpB = Math.max(0, hpB - damage);
      }

      timeline.push({
        event: 'hit',
        round,
        turn,
        attacker,
        defender,
        damage,
        defender_hp: defender === 'A' ? hpA : hpB,
      });

      if (hpA <= 0 || hpB <= 0) {
        const koDefender = hpA <= 0 ? 'A' : 'B';
        timeline.push({
          event: 'ko',
          round,
          turn: turn + 1,
          attacker: koDefender === 'A' ? 'B' : 'A',
          defender: koDefender,
          damage: 0,
          defender_hp: 0,
        });
        break;
      }

      turn++;
    }

    mockBattle.timeline = timeline;
    mockBattle.winner_slot = hpA > hpB ? 'A' : 'B';
    mockBattle.wins[mockBattle.winner_slot] = 1;

    return mockBattle;
  };

  // Show battle view if battle started
  if (showBattleView && battleResult) {
    return (
      <BattleView
        battle={battleResult}
        liveEvents={liveEvents}
        latestMonsters={latestMonsters}
        latestSkills={latestSkills}
        onClose={() => {
          setShowBattleView(false);
          setShowSummary(true);
        }}
      />
    );
  }

  return (
    <div className="match-screen" style={matchStyle}>
      <Head>
        <title>Sketch Brawl Match</title>
      </Head>
      <section className="match-hero" data-node-id="42:1961">
        <h1 data-node-id="42:2003">{phaseTitle}</h1>
        <div className="player-grid" data-node-id="42:1965">
          {playerPanels[0]}
          <div className="match-center-column">
            <div className="match-arrow" aria-hidden>
              <svg viewBox="0 0 160 40" role="presentation">
                <path d="M10 20 H150" />
                <path d="M20 10 L10 20 L20 30" />
                <path d="M140 10 L150 20 L140 30" />
              </svg>
              <span>draw here</span>
            </div>
            <div className="match-tools">
              <button
                className={`match-tool match-tool--pencil ${toolMode === 'pen' ? 'active' : ''}`}
                aria-label="pencil"
                onClick={() => setToolMode('pen')}
              >
                <img src="/ui/pen.svg" alt="pencil" />
              </button>
              <button
                className={`match-tool match-tool--eraser ${toolMode === 'eraser' ? 'active' : ''}`}
                aria-label="eraser"
                onClick={() => setToolMode('eraser')}
              >
                <img src="/ui/eraser.svg" alt="eraser" />
              </button>
            </div>
          </div>
          {playerPanels[1]}
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
            onClick={() => {
              try {
                setError(null);
                setStatus('battling');
                // Use mock battle for frontend testing
                const battle = startMockBattle();
                setBattleResult(battle);
                setShowBattleView(true);
                setStatus('ready');
              } catch (err) {
                console.error(err);
                setError((err as Error).message);
                setStatus('ready');
              }
            }}
          >
            Start Battle (Mock)
          </button>
          <button
            onClick={() => {
              try {
                setError(null);
                // Generate fake monsters and skills if they don't exist
                if (!latestMonsters.A) {
                  setLatestMonsters({
                    A: {
                      name: 'Weird Bunny',
                      element: 'Wood',
                      hp: 85,
                      attack: 14,
                      defence: 94,
                      snapshot: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzIyYzU1ZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPldlaXJkIEJ1bm55PC90ZXh0Pjwvc3ZnPg==',
                    },
                    B: {
                      name: 'Angry Turtle',
                      element: 'Water',
                      hp: 100,
                      attack: 18,
                      defence: 94,
                      snapshot: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzNiODJmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkFuZ3J5IFR1cnRsZTwvdGV4dD48L3N2Zz4=',
                    },
                  });
                }
                if (!latestSkills.A) {
                  setLatestSkills({
                    A: {
                      name: 'Flame Sword',
                      element: 'Fire',
                      attack_move: 'Fire Slay',
                      power: 25,
                      card_snapshot: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VmNDQ0NCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZsYW1lIFN3b3JkPC90ZXh0Pjwvc3ZnPg==',
                    },
                    B: {
                      name: 'Moai Shield',
                      element: 'Earth',
                      attack_move: 'Rock Smash',
                      power: 20,
                      card_snapshot: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y5NzMxNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk1vYWkgU2hpZWxkPC90ZXh0Pjwvc3ZnPg==',
                    },
                  });
                }
                // Start battle with fake data
                setTimeout(() => {
                  const battle = startMockBattle();
                  setBattleResult(battle);
                  setShowBattleView(true);
                  setStatus('ready');
                }, 100);
              } catch (err) {
                console.error(err);
                setError((err as Error).message);
              }
            }}
          >
            Quick Test Battle
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

type BattleViewProps = {
  battle: BattleResponse;
  liveEvents: BattleEvent[];
  latestMonsters: Record<'A' | 'B', Record<string, any> | null>;
  latestSkills: Record<'A' | 'B', Record<string, any> | null>;
  onClose: () => void;
};

function BattleView({ battle, liveEvents, latestMonsters, latestSkills, onClose }: BattleViewProps) {
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [playerHPs, setPlayerHPs] = useState<Record<'A' | 'B', { current: number; max: number }>>({
    A: { current: 0, max: 0 },
    B: { current: 0, max: 0 },
  });
  const [battleLog, setBattleLog] = useState<string[]>(['Battle start!']);
  const [isComplete, setIsComplete] = useState(false);
  const battleLogRef = useRef<HTMLDivElement>(null);

  // Initialize HPs from battle combatants
  useEffect(() => {
    const hps: Record<'A' | 'B', { current: number; max: number }> = { A: { current: 0, max: 0 }, B: { current: 0, max: 0 } };
    battle.combatants.forEach((combatant) => {
      const slot = combatant.slot as 'A' | 'B';
      hps[slot] = {
        current: combatant.base_hp,
        max: combatant.base_hp,
      };
    });
    setPlayerHPs(hps);
  }, [battle]);

  // Animate through battle events
  useEffect(() => {
    if (!battle.timeline.length) return;
    if (currentEventIndex >= battle.timeline.length) {
      setIsComplete(true);
      return;
    }

    const timer = setTimeout(() => {
      const event = battle.timeline[currentEventIndex];
      const attacker = battle.combatants.find((c) => c.slot === event.attacker);
      const defender = battle.combatants.find((c) => c.slot === event.defender);

      let logMessage = '';
      if (event.event === 'hit') {
        logMessage = `${attacker?.name || event.attacker} attacked ${defender?.name || event.defender}!`;
        setBattleLog((prev) => [...prev, logMessage]);
        
        if (event.damage > 0) {
          logMessage = `${defender?.name || event.defender} took ${event.damage} damage!`;
          setBattleLog((prev) => [...prev, logMessage]);
          
          // Update HP
          const defenderSlot = event.defender as 'A' | 'B';
          setPlayerHPs((prev) => ({
            ...prev,
            [defenderSlot]: {
              ...prev[defenderSlot],
              current: Math.max(0, event.defender_hp),
            },
          }));
        }
      } else if (event.event === 'ko') {
        logMessage = `${defender?.name || event.defender} was knocked out!`;
        setBattleLog((prev) => [...prev, logMessage]);
      } else if (event.event === 'round_end') {
        logMessage = `Round ${event.round} ended!`;
        setBattleLog((prev) => [...prev, logMessage]);
      }

      setCurrentEventIndex((prev) => prev + 1);
    }, 1500);

    return () => clearTimeout(timer);
  }, [currentEventIndex, battle]);

  // Auto-scroll battle log
  useEffect(() => {
    if (battleLogRef.current) {
      battleLogRef.current.scrollTop = battleLogRef.current.scrollHeight;
    }
  }, [battleLog]);

  const getCombatant = (slot: 'A' | 'B') => battle.combatants.find((c) => c.slot === slot);
  const combatantA = getCombatant('A');
  const combatantB = getCombatant('B');

  const buildMonsterData = (slot: 'A' | 'B') => {
    const combatant = getCombatant(slot);
    const monster = latestMonsters[slot];
    const skill = latestSkills[slot];
    const elementPrimary =
      monster?.element ?? monster?.primary_element ?? combatant?.element ?? 'mystery';
    const elementSecondary = skill?.element ?? monster?.secondary_element ?? null;
    return {
      name: monster?.name ?? combatant?.name ?? `Player ${slot}`,
      elementPrimary,
      elementSecondary,
      hp: monster?.hp ?? monster?.base_hp ?? combatant?.base_hp ?? 0,
      attack: monster?.attack ?? combatant?.base_attack ?? 0,
      defence:
        monster?.defence ??
        (typeof combatant?.defence === 'number' ? combatant.defence : undefined) ??
        0,
      snapshot: monster?.snapshot ?? monster?.image ?? combatant?.snapshot ?? null,
    };
  };

  const buildSkillData = (slot: 'A' | 'B') => {
    const combatant = getCombatant(slot);
    const skill = latestSkills[slot];
    const fallbackSkill = combatant?.skills?.[0];
    if (!skill && !fallbackSkill) return null;
    return {
      name: skill?.name ?? fallbackSkill?.name ?? 'Skill',
      element: skill?.element ?? fallbackSkill?.element ?? combatant?.element ?? 'mystery',
      attack_move:
        skill?.attack_move ??
        fallbackSkill?.attack_move ??
        fallbackSkill?.name ??
        'Attack',
      power: skill?.power ?? fallbackSkill?.power ?? combatant?.skill_power ?? 0,
      card_snapshot:
        skill?.card_snapshot ??
        skill?.snapshot ??
        fallbackSkill?.card_snapshot ??
        fallbackSkill?.snapshot ??
        combatant?.snapshot ??
        null,
    };
  };

  const monsters = {
    A: buildMonsterData('A'),
    B: buildMonsterData('B'),
  };

  const skills = {
    A: buildSkillData('A'),
    B: buildSkillData('B'),
  };

  const winnerName =
    battle.winner_slot === 'A' ? monsters.A.name : monsters.B.name;

  return (
    <div className="battle-view" style={{ '--match-texture': `url(${matchTexture})` } as CSSVarStyle}>
      <Head>
        <title>Battle - Sketch Brawl</title>
      </Head>

      {/* VS Header */}
      <div className="battle-header">
        <h1 className="battle-player-name">{combatantA?.name || 'Player A'}</h1>
        <h1 className="battle-vs">~VS~</h1>
        <h1 className="battle-player-name">{combatantB?.name || 'Player B'}</h1>
      </div>

      {/* Main Battle Layout */}
      <div className="battle-main-grid">
        {/* Player A Side */}
        <div className="battle-player-column">
          {/* HP Bar */}
          <div className="battle-hp-section">
            <p className="battle-hp-text">
              HP {playerHPs.A.current}/{playerHPs.A.max}
            </p>
            <div className="battle-hp-bar-container">
              <div className="battle-hp-bar-bg" />
              <div
                className="battle-hp-bar-fill"
                style={{
                  width: `${Math.max(0, (playerHPs.A.current / playerHPs.A.max) * 100)}%`,
                }}
              />
            </div>
          </div>

          {/* Monster Display - No frame */}
          <div className="battle-monster-display">
            {monsters.A.snapshot && (
              <img src={monsters.A.snapshot} alt={monsters.A.name} />
            )}
          </div>

          {/* Monster Stats Card */}
          <div className="battle-stats-card">
            <h3 className="battle-stats-title">{monsters.A.name}</h3>
            <div className="battle-stats-divider" />
            <div className="battle-stats-grid">
              <p className="battle-stat-label">
                {monsters.A.elementPrimary}
                {monsters.A.elementSecondary ? ` + ${monsters.A.elementSecondary}` : ''}
              </p>
              <p className="battle-stat-value">HP {monsters.A.hp}</p>
              <p className="battle-stat-label" />
              <p className="battle-stat-value">Attack {monsters.A.attack}</p>
              <p className="battle-stat-label" />
              <p className="battle-stat-value">Defence {monsters.A.defence}</p>
            </div>
          </div>

          {/* Gear Card */}
          {skills.A && (
            <div className="battle-gear-card">
              <h3 className="battle-gear-title">{skills.A.name}</h3>
              <div className="battle-stats-divider" />
              <div className="battle-gear-layout">
                <div className="battle-gear-text">
                  <p className="battle-stat-label">{skills.A.element}</p>
                  <p className="battle-stat-value">Attack</p>
                  <p className="battle-stat-value">{skills.A.attack_move}!</p>
                  <p className="battle-stat-value">Power {skills.A.power}</p>
                </div>
                <div className="battle-gear-frame">
                  {skills.A.card_snapshot && (
                    <img src={skills.A.card_snapshot} alt={`${skills.A.name} card`} />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Center Column */}
        <div className="battle-center-column">
          <div className="battle-center-banner">
            <p className="battle-center-title">
              {isComplete ? `${winnerName} Wins!` : 'Battle In Progress'}
            </p>
            {isComplete && (
              <button className="battle-victory-button" onClick={onClose}>
                READY TO UPGRADE!
              </button>
            )}
          </div>
          <div className="battle-log-card">
            <h3 className="battle-log-title">BATTLE LOG</h3>
            <div className="battle-log-content" ref={battleLogRef}>
              <ul className="battle-log-list">
                {battleLog.map((log, idx) => (
                  <li key={idx} className="battle-log-item">
                    {log}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Player B Side */}
        <div className="battle-player-column">
          {/* HP Bar */}
          <div className="battle-hp-section">
            <p className="battle-hp-text battle-hp-text-right">
              HP {playerHPs.B.current}/{playerHPs.B.max}
            </p>
            <div className="battle-hp-bar-container">
              <div className="battle-hp-bar-bg" />
              <div
                className="battle-hp-bar-fill battle-hp-bar-fill-right"
                style={{
                  width: `${Math.max(0, (playerHPs.B.current / playerHPs.B.max) * 100)}%`,
                }}
              />
            </div>
          </div>

          {/* Monster Display - No frame */}
          <div className="battle-monster-display">
            {monsters.B.snapshot && (
              <img src={monsters.B.snapshot} alt={monsters.B.name} />
            )}
          </div>

          {/* Monster Stats Card */}
          <div className="battle-stats-card">
            <h3 className="battle-stats-title">{monsters.B.name}</h3>
            <div className="battle-stats-divider" />
            <div className="battle-stats-grid">
              <p className="battle-stat-label">
                {monsters.B.elementPrimary}
                {monsters.B.elementSecondary ? ` + ${monsters.B.elementSecondary}` : ''}
              </p>
              <p className="battle-stat-value">HP {monsters.B.hp}</p>
              <p className="battle-stat-label" />
              <p className="battle-stat-value">Attack {monsters.B.attack}</p>
              <p className="battle-stat-label" />
              <p className="battle-stat-value">Defence {monsters.B.defence}</p>
            </div>
          </div>

          {/* Gear Card */}
          {skills.B && (
            <div className="battle-gear-card">
              <h3 className="battle-gear-title">{skills.B.name}</h3>
              <div className="battle-stats-divider" />
              <div className="battle-gear-layout">
                <div className="battle-gear-text">
                  <p className="battle-stat-label">{skills.B.element}</p>
                  <p className="battle-stat-value">Attack</p>
                  <p className="battle-stat-value">{skills.B.attack_move}!</p>
                  <p className="battle-stat-value">Power {skills.B.power}</p>
                </div>
                <div className="battle-gear-frame">
                  {skills.B.card_snapshot && (
                    <img src={skills.B.card_snapshot} alt={`${skills.B.name} card`} />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
