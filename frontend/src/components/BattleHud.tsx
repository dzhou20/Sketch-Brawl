'use client';

import { useMemo, type FC } from 'react';
import type { BattleEvent, BattleResponse, CombatantPayload, RoundSummary } from '@/services/apiClient';

const eventLabel: Record<string, string> = {
  hit: 'Hit',
  ko: 'KO',
  round_end: 'Round End',
};

type Props = {
  battle: BattleResponse | null;
  liveEvents?: BattleEvent[];
};

export const BattleHud: FC<Props> = ({ battle, liveEvents = [] }) => {
  const eventsByRound = useMemo(() => {
    if (!battle) return {};
    return battle.timeline.reduce<Record<number, BattleEvent[]>>((acc, event) => {
      if (!acc[event.round]) acc[event.round] = [];
      acc[event.round].push(event);
      return acc;
    }, {});
  }, [battle]);

  if (!battle) {
    return (
      <section className="battle-hud empty">
        <h2>Battle Timeline</h2>
        <p>Draw monsters for both players, then start a battle to see the timeline.</p>
      </section>
    );
  }

  return (
    <section className="battle-hud">
      <header>
        <div className="battle-header">
          <div>
            <h2>Battle {battle.battle_id}</h2>
            <p>Winner: {battle.winner_slot}</p>
          </div>
          <div className="score">{formatScore(battle.wins)}</div>
        </div>
      </header>
      <div className="combatant-grid">
        {battle.combatants.map((combatant) => (
          <CombatantCard
            key={combatant.slot}
            combatant={combatant}
            isWinner={battle.winner_slot === combatant.slot}
          />
        ))}
      </div>
      <div className="round-grid">
        {battle.rounds.map((round) => (
          <RoundCard
            key={round.round}
            round={round}
            events={eventsByRound[round.round] ?? []}
            liveEvents={liveEvents}
          />
        ))}
      </div>
    </section>
  );
};

const CombatantCard: FC<{ combatant: CombatantPayload; isWinner: boolean }> = ({ combatant, isWinner }) => {
  return (
    <article className={`combatant-card ${isWinner ? 'winner' : ''}`}>
      <div className="card-header">
        <span className="slot">{combatant.slot}</span>
        <div>
          <strong>{combatant.name}</strong>
          <p>{combatant.element} element</p>
        </div>
      </div>
      {combatant.snapshot && <img src={combatant.snapshot} alt={`${combatant.name} snapshot`} />}
      <dl className="stats">
        <div>
          <dt>HP</dt>
          <dd>{combatant.base_hp}</dd>
        </div>
        <div>
          <dt>Attack</dt>
          <dd>{combatant.base_attack}</dd>
        </div>
        <div>
          <dt>Skill Power</dt>
          <dd>{combatant.skill_power}</dd>
        </div>
      </dl>
      {combatant.skills.length > 0 && (
        <ul className="skill-list">
          {combatant.skills.map((skill) => (
            <li key={skill.id || skill.name}>
              <span>{skill.type}</span>
              <em>+{skill.attack_bonus} atk</em>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
};

const RoundCard: FC<{ round: RoundSummary; events: BattleEvent[]; liveEvents: BattleEvent[] }> = ({
  round,
  events,
  liveEvents,
}) => (
  <article className="round-card">
    <header>
      <div>
        <h3>Round {round.round}</h3>
        <p>Winner: {round.winner_slot || '—'}</p>
      </div>
      <div className="round-meta">
        <span>{round.turns} turns</span>
        {round.ko_turn ? <span>KO on turn {round.ko_turn}</span> : <span>No KO</span>}
      </div>
    </header>
    <div className="round-stats">
      {Object.entries(round.total_damage).map(([slot, damage]) => (
        <div key={slot}>
          <small>{slot} dmg</small>
          <strong>{damage}</strong>
        </div>
      ))}
    </div>
    <div className="round-events">
      {events.map((event, idx) => {
        const isLive = liveEvents.some((live) => live.round === event.round && live.turn === event.turn);
        return (
          <div key={`${event.round}-${event.turn}-${idx}`} className={`event ${event.event} ${isLive ? 'active' : ''}`}>
            <div className="meta">
              <span>Turn {event.turn}</span>
              <span>{eventLabel[event.event] ?? event.event}</span>
            </div>
            <div className="summary">
              <strong>{event.attacker}</strong>
              {event.defender !== '-' && (
                <>
                  <span>→ {event.defender}</span>
                  <span>-{event.damage} HP (rem {event.defender_hp})</span>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  </article>
);

function formatScore(wins: Record<string, number>): string {
  return Object.entries(wins)
    .map(([slot, count]) => `${slot}: ${count}`)
    .join(' · ');
}
