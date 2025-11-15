'use client';

type Props = {
  payload: Record<string, any> | null;
  doodleType: 'monster' | 'skill' | 'reinforcement';
};

type MonsterMove = {
  name?: string;
  description?: string;
  kind?: string;
  element?: string;
  power?: number;
};

const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value) || typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
};

const extractMoves = (payload: Record<string, any>): MonsterMove[] => {
  if (!payload.moves || !Array.isArray(payload.moves)) return [];
  return payload.moves.filter((move: unknown): move is MonsterMove => typeof move === 'object' && move !== null);
};

const MonsterDetails = ({ payload }: { payload: Record<string, any> }) => {
  const moves = extractMoves(payload);
  const stats = [
    { label: 'Element', value: payload.element },
    { label: 'Species', value: payload.species },
    { label: 'HP', value: payload.hp },
    { label: 'Attack', value: payload.base_attack ?? payload.attack },
    { label: 'Defense', value: payload.defense },
    { label: 'Seed', value: payload.seed },
  ].filter((stat) => stat.value !== undefined && stat.value !== null);

  return (
    <div className="monster-details">
      <div className="summary">
        <h3>{payload.name ?? 'Unnamed Monster'}</h3>
        {payload.species && <p className="species">{payload.species}</p>}
        {payload.description && <p className="description">{payload.description}</p>}
      </div>
      <dl className="stat-grid">
        {stats.map((stat) => (
          <div key={stat.label}>
            <dt>{stat.label}</dt>
            <dd>{String(stat.value)}</dd>
          </div>
        ))}
      </dl>
      {moves.length > 0 && (
        <div className="moves">
          <h4>Moves</h4>
          <ul>
            {moves.map((move, idx) => (
              <li key={move.name ?? idx}>
                <strong>{move.name ?? `Move ${idx + 1}`}</strong>
                <p>{move.description}</p>
                <small>
                  {move.kind && `${move.kind} · `}
                  {move.element && `${move.element} · `}
                  {move.power !== undefined && `Power ${move.power}`}
                </small>
              </li>
            ))}
          </ul>
        </div>
      )}
      {payload.explanation && <p className="explanation">Reasoning: {payload.explanation}</p>}
    </div>
  );
};

const SkillDetails = ({ payload }: { payload: Record<string, any> }) => {
  const stats = [
    { label: 'Element', value: payload.element },
    { label: 'Type', value: payload.skill_type || payload.kind },
    { label: 'Power', value: payload.attack_bonus ?? payload.power },
    { label: 'Cooldown Δ', value: payload.cooldown_delta },
    { label: 'Seed', value: payload.seed },
  ].filter((stat) => stat.value !== undefined && stat.value !== null);

  return (
    <div className="skill-details">
      <div className="summary">
        <h3>{payload.name ?? 'Unnamed Skill'}</h3>
        {payload.description && <p className="description">{payload.description}</p>}
      </div>
      <dl className="stat-grid">
        {stats.map((stat) => (
          <div key={stat.label}>
            <dt>{stat.label}</dt>
            <dd>{String(stat.value)}</dd>
          </div>
        ))}
      </dl>
      {payload.explanation && <p className="explanation">Reasoning: {payload.explanation}</p>}
    </div>
  );
};

const GenericDetails = ({ payload }: { payload: Record<string, any> }) => {
  const entries = Object.entries(payload).filter(([, value]) => value !== undefined && value !== null);
  return (
    <dl>
      {entries.map(([key, value]) => (
        <div key={key} className="row">
          <dt>{key}</dt>
          <dd>{formatValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
};

const RawPayload = ({ payload }: { payload: Record<string, any> }) => (
  <details className="raw-payload">
    <summary>Raw Payload</summary>
    <pre>{JSON.stringify(payload, null, 2)}</pre>
  </details>
);

export function AttributionPanel({ payload, doodleType }: Props) {
  const renderDetails = () => {
    if (!payload) return null;
    if (doodleType === 'monster') return <MonsterDetails payload={payload} />;
    if (doodleType === 'skill') return <SkillDetails payload={payload} />;
    return <GenericDetails payload={payload} />;
  };

  return (
    <section className="attribution-panel">
      <header>
        <h2>{doodleType.toUpperCase()} Attributes</h2>
      </header>
      {!payload && <p>Submit a doodle to view AI interpretation.</p>}
      {payload && (
        <>
          {renderDetails()}
          <RawPayload payload={payload} />
        </>
      )}
    </section>
  );
}
