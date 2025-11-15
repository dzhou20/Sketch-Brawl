'use client';

import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/services/apiClient';
import { telemetryPublisher } from '@/services/telemetryPublisher';

type DoodleType = 'monster' | 'skill' | 'reinforcement';

type Stroke = {
  x: number;
  y: number;
  pressure?: number;
  timestamp: number;
};

type Props = {
  lobbyId: string | null;
  playerSlot: 'A' | 'B';
  doodleType: DoodleType;
  onResult: (payload: any) => void;
  metadataOverrides?: Record<string, unknown>;
  onSubmitStateChange?: (state: 'idle' | 'submitting' | 'complete') => void;
  strokeColor?: string;
  backgroundColor?: string;
  submitLabel?: string;
  clearLabel?: string;
};

const CANVAS_SIZE = 480;

export function DoodleCanvas({
  lobbyId,
  playerSlot,
  doodleType,
  onResult,
  metadataOverrides,
  onSubmitStateChange,
  strokeColor = '#ffeb3b',
  backgroundColor = '#1f1f1f',
  submitLabel,
  clearLabel,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const strokesRef = useRef<Stroke[]>([]);
  const drawingRef = useRef(false);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const [status, setStatus] = useState<string>('Ready to sketch');

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    canvas.width = CANVAS_SIZE;
    canvas.height = CANVAS_SIZE;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.lineWidth = 4;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    ctx.beginPath();
    ctxRef.current = ctx;

    const handlePointerDown = (event: PointerEvent) => {
      drawingRef.current = true;
      const stroke = toStroke(event, canvas);
      const ctxLocal = ctxRef.current;
      if (ctxLocal) {
        ctxLocal.beginPath();
        ctxLocal.moveTo(stroke.x, stroke.y);
      }
      strokesRef.current.push(stroke);
    };

    const handlePointerMove = (event: PointerEvent) => {
      if (!drawingRef.current) return;
      const stroke = toStroke(event, canvas);
      const ctxLocal = ctxRef.current;
      if (ctxLocal) {
        ctxLocal.lineTo(stroke.x, stroke.y);
        ctxLocal.stroke();
      }
      strokesRef.current.push(stroke);
    };

    const handlePointerUp = () => {
      drawingRef.current = false;
      ctx.beginPath();
    };

    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);

    return () => {
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [strokeColor, backgroundColor]);

  useEffect(() => {
    if (lobbyId) {
      telemetryPublisher.start(lobbyId);
    }
  }, [lobbyId]);

  const submitDoodle = async () => {
    if (!lobbyId) {
      setStatus('Waiting for lobby...');
      return;
    }
    if (!strokesRef.current.length) {
      setStatus('Draw something before submitting');
      return;
    }
    setStatus('Submitting doodle...');
    onSubmitStateChange?.('submitting');
    try {
      const snapshot = canvasRef.current?.toDataURL('image/png');
      const ticket = await apiClient.submitDoodle({
        lobby_id: lobbyId,
        doodle_type: doodleType,
        strokes: strokesRef.current,
        metadata: buildMetadata(),
        snapshot,
      });
      const result = await pollInference(ticket.ticket_id);
      onResult(result);
      setStatus('Inference complete');
      onSubmitStateChange?.('complete');
      clearCanvas();
    } catch (error: any) {
      setStatus(error?.message ?? 'Submission failed');
      onSubmitStateChange?.('idle');
    }
  };

  const clearCanvas = () => {
    const ctx = ctxRef.current;
    if (ctx) {
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
      ctx.strokeStyle = strokeColor;
      ctx.beginPath();
    }
    strokesRef.current = [];
  };

  const pollInference = async (ticketId: string) => {
    for (;;) {
      const response = await apiClient.getInference(ticketId);
      if (response.ready && response.payload) {
        return response.payload;
      }
      const waitingCopy = response.waiting_for
        ? response.waiting_for === 'both'
          ? 'Waiting for both players…'
          : `Waiting for Player ${response.waiting_for}…`
        : 'Waiting for players…';
      setStatus(waitingCopy);
      await wait(1000);
    }
  };

  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const buildMetadata = () => {
    const merged: Record<string, unknown> = { player_slot: playerSlot, ...(metadataOverrides ?? {}) };
    Object.keys(merged).forEach((key) => {
      if (merged[key] === undefined || merged[key] === null) {
        delete merged[key];
      }
    });
    return merged;
  };

  const toStroke = (event: PointerEvent, canvas: HTMLCanvasElement): Stroke => {
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      pressure: event.pressure,
      timestamp: Date.now(),
    };
  };

  return (
    <div className="doodle-canvas">
      <canvas ref={canvasRef} />
      <div className="actions">
        <button onClick={submitDoodle}>{submitLabel ?? `Submit ${doodleType}`}</button>
        <button onClick={clearCanvas}>{clearLabel ?? 'Clear'}</button>
      </div>
      <p>{status}</p>
    </div>
  );
}
