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
  doodleType: DoodleType;
  onResult: (payload: any) => void;
};

const CANVAS_SIZE = 480;

export function DoodleCanvas({ lobbyId, doodleType, onResult }: Props) {
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
    ctx.strokeStyle = '#ffeb3b';
    ctx.fillStyle = '#1f1f1f';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    ctxRef.current = ctx;

    const handlePointerDown = (event: PointerEvent) => {
      drawingRef.current = true;
      strokesRef.current.push(toStroke(event, canvas));
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
  }, []);

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
    try {
      const ticket = await apiClient.submitDoodle({
        lobby_id: lobbyId,
        doodle_type: doodleType,
        strokes: strokesRef.current,
      });
      const result = await pollInference(ticket.ticket_id);
      onResult(result);
      setStatus('Inference complete');
      clearCanvas();
    } catch (error: any) {
      setStatus(error?.message ?? 'Submission failed');
    }
  };

  const clearCanvas = () => {
    const ctx = ctxRef.current;
    if (ctx) {
      ctx.fillStyle = '#1f1f1f';
      ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
      ctx.beginPath();
    }
    strokesRef.current = [];
  };

  const pollInference = async (ticketId: string) => {
    for (let i = 0; i < 10; i += 1) {
      const response = await apiClient.getInference(ticketId);
      if (response.payload) {
        return response.payload;
      }
      await wait(500);
    }
    throw new Error('Inference timeout');
  };

  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

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
        <button onClick={submitDoodle}>Submit {doodleType}</button>
        <button onClick={clearCanvas}>Clear</button>
      </div>
      <p>{status}</p>
    </div>
  );
}
