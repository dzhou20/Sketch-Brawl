'use client';

import { useEffect, useMemo, useState } from 'react';
import type { BattleEvent } from '@/services/apiClient';

export type StageFighter = {
  slot: 'A' | 'B';
  name: string;
  element?: string | null;
  snapshot?: string | null;
};

const emptyCopy = {
  title: '等待战斗开始',
  subtitle: '画好双方的怪物并发起战斗，舞台就会播放每一次出手。',
};

export function BattleStage({
  fighters,
  events,
}: {
  fighters: StageFighter[];
  events: BattleEvent[];
}) {
  const [activeEvent, setActiveEvent] = useState<BattleEvent | null>(null);
  const [attackingSlot, setAttackingSlot] = useState<string | null>(null);
  const [hitSlot, setHitSlot] = useState<string | null>(null);

  useEffect(() => {
    if (!events.length) return;
    setActiveEvent(events[events.length - 1]);
  }, [events]);

  useEffect(() => {
    if (!activeEvent) return;
    setAttackingSlot(activeEvent.attacker);
    setHitSlot(activeEvent.defender !== '-' ? activeEvent.defender : null);
    const timeout = setTimeout(() => {
      setAttackingSlot(null);
      setHitSlot(null);
    }, 650);
    return () => clearTimeout(timeout);
  }, [activeEvent?.round, activeEvent?.turn]);

  const fighterLookup = useMemo(() => {
    const map: Record<string, StageFighter> = {};
    fighters.forEach((fighter) => {
      map[fighter.slot] = fighter;
    });
    return map;
  }, [fighters]);

  const sortedFighters = useMemo(() => {
    return [...fighters].sort((a, b) => (a.slot < b.slot ? -1 : 1));
  }, [fighters]);

  const callout = useMemo(() => {
    if (!activeEvent) return emptyCopy.subtitle;
    if (activeEvent.event === 'round_end') {
      return `回合 ${activeEvent.round} 结束，${activeEvent.attacker} 获胜。`;
    }
    const attacker = fighterLookup[activeEvent.attacker]?.name ?? `玩家 ${activeEvent.attacker}`;
    const defender =
      activeEvent.defender !== '-'
        ? fighterLookup[activeEvent.defender]?.name ?? `玩家 ${activeEvent.defender}`
        : '战场';
    return `${attacker} 攻击 ${defender} ，造成 ${activeEvent.damage} 伤害 (剩余 ${activeEvent.defender_hp})`;
  }, [activeEvent, fighterLookup]);

  if (sortedFighters.length < 2) {
    return (
      <section className="battle-stage">
        <div className="battle-stage__empty">
          <p className="eyebrow">battle stage</p>
          <h3>{emptyCopy.title}</h3>
          <p>{emptyCopy.subtitle}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="battle-stage">
      <header>
        <p className="eyebrow">battle stage</p>
        {activeEvent ? (
          <span>
            Round {activeEvent.round} · Turn {activeEvent.turn}
          </span>
        ) : (
          <span>准备完毕即可播放实时击打</span>
        )}
      </header>
      <div className="arena">
        {sortedFighters.map((fighter) => (
          <div
            key={fighter.slot}
            className={[
              'fighter',
              fighter.slot === 'A' ? 'left' : 'right',
              attackingSlot === fighter.slot ? 'attacking' : '',
              hitSlot === fighter.slot ? 'hit' : '',
            ]
              .filter(Boolean)
              .join(' ')}
          >
            {fighter.snapshot ? (
              <img src={fighter.snapshot} alt={`${fighter.name} portrait`} />
            ) : (
              <div className="placeholder">{fighter.name ? fighter.name.charAt(0).toUpperCase() : '?'}</div>
            )}
            <div className="label">
              <strong>{fighter.name}</strong>
              <span>{fighter.element ?? 'mystery'}</span>
            </div>
          </div>
        ))}
        {activeEvent && activeEvent.event !== 'round_end' && (
          <div className={`impact ${activeEvent.event}`}>
            <span>{activeEvent.event === 'ko' ? 'KO!' : `-${activeEvent.damage}`}</span>
          </div>
        )}
      </div>
      <p className="callout">{callout}</p>
    </section>
  );
}
