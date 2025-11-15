'use client';

import { useMemo } from 'react';

type Props = {
  payload: Record<string, any> | null;
  doodleType: 'monster' | 'skill' | 'reinforcement';
};

export function AttributionPanel({ payload, doodleType }: Props) {
  const entries = useMemo(() => {
    if (!payload) return [];
    return Object.entries(payload).filter(([, value]) => value !== undefined && value !== null);
  }, [payload]);

  return (
    <section className="attribution-panel">
      <header>
        <h2>{doodleType.toUpperCase()} Attributes</h2>
      </header>
      {!payload && <p>Submit a doodle to view AI interpretation.</p>}
      {payload && (
        <dl>
          {entries.map(([key, value]) => (
            <div key={key} className="row">
              <dt>{key}</dt>
              <dd>{typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
