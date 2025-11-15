'use client';

import { useEffect, useRef, useState } from 'react';
import { apiClient, type BattleEvent } from '@/services/apiClient';

export function useBattleStream(battleId: number | null) {
  const [events, setEvents] = useState<BattleEvent[]>([]);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!battleId) {
      setEvents([]);
      return;
    }
    const unsub = apiClient.subscribeBattleStream(battleId, (evt) => {
      setEvents((prev) => [...prev, evt]);
    });
    unsubscribeRef.current = unsub;
    return () => {
      unsub?.();
      unsubscribeRef.current = null;
    };
  }, [battleId]);

  return { events, reset: () => setEvents([]) };
}
