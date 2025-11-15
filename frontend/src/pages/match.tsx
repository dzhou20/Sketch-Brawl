'use client';

import { useEffect, useState } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { apiClient } from '@/services/apiClient';
import { DoodleCanvas } from '@/components/DoodleCanvas';
import { AttributionPanel } from '@/components/AttributionPanel';

const doodleOptions = ['monster', 'skill', 'reinforcement'] as const;

export default function MatchPage() {
  const { lobbyId, ensureLobby } = useSessionStore();
  const [status, setStatus] = useState('bootstrapping');
  const [doodleType, setDoodleType] = useState<(typeof doodleOptions)[number]>('monster');
  const [payload, setPayload] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    async function bootstrap() {
      setStatus('joining');
      await ensureLobby();
      setStatus('ready');
    }
    bootstrap();
  }, [ensureLobby]);

  return (
    <div className="match-layout">
      <header>
        <h1>Sketch Brawl Lobby {lobbyId ?? '...'}</h1>
        <p>Status: {status}</p>
        <button onClick={() => apiClient.health()}>API Health</button>
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
        <DoodleCanvas lobbyId={lobbyId} doodleType={doodleType} onResult={setPayload} />
        <AttributionPanel payload={payload} doodleType={doodleType} />
      </div>
    </div>
  );
}
