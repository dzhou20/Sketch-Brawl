'use client';

type SkillPayload = Record<string, any> | null;

type Props = {
  skill: SkillPayload;
  slot: 'A' | 'B';
  onReinforce: () => void;
};

export function SkillCardPanel({ skill, slot, onReinforce }: Props) {
  if (!skill) {
    return (
      <section className="skill-panel empty">
        <header>
          <h3>Player {slot} Skill</h3>
        </header>
        <p>Draw a skill to unlock reinforcements.</p>
      </section>
    );
  }

  const historyEntries: Array<Record<string, any>> = [];
  if (Array.isArray(skill.history)) {
    skill.history.forEach((entry: any) => {
      if (typeof entry === 'string') {
        try {
          historyEntries.push(JSON.parse(entry));
        } catch (_err) {
          // ignore invalid entry
        }
      } else if (entry && typeof entry === 'object') {
        historyEntries.push(entry);
      }
    });
  }

  return (
    <section className="skill-panel">
      <header>
        <h3>
          Player {slot} Skill #{skill.skill_id ?? '—'}
        </h3>
        <button onClick={onReinforce}>Reinforce</button>
      </header>
      <dl>
        <div>
          <dt>Type</dt>
          <dd>{skill.skill_type || 'weapon'}</dd>
        </div>
        <div>
          <dt>Element(s)</dt>
          <dd>{Array.isArray(skill.elements) ? skill.elements.join(', ') : skill.element}</dd>
        </div>
        <div>
          <dt>Attack Bonus</dt>
          <dd>{skill.attack_bonus}</dd>
        </div>
      </dl>
      {historyEntries.length > 0 && (
        <div className="history">
          <h4>Reinforcements</h4>
          <ul>
            {historyEntries.map((entry, idx) => (
              <li key={`${slot}-reinforce-${idx}`}>
                <span>{entry.skill_type || entry.target || 'buff'}</span>
                <small>+{entry.attack_bonus || 0} atk / +{entry.hp || 0} hp</small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
