'use client';

import { useEffect, useRef, useState, useImperativeHandle, forwardRef, useCallback } from 'react';
import { apiClient } from '@/services/apiClient';
import { telemetryPublisher } from '@/services/telemetryPublisher';

type DoodleType = 'monster' | 'skill' | 'reinforcement';

type Stroke = {
  x: number;
  y: number;
  pressure?: number;
  timestamp: number;
};

type ToolMode = 'pen' | 'eraser';

export type DoodleCanvasRef = {
  submit: () => Promise<void>;
  clear: () => void;
  getStrokes: () => Stroke[];
  getSnapshot: () => string | null;
};

type ResultContext = {
  snapshot?: string | null;
  doodleType: DoodleType;
  slot: 'A' | 'B';
};

type Props = {
  lobbyId: string | null;
  playerSlot: 'A' | 'B';
  doodleType: DoodleType;
  onResult: (payload: any, context: ResultContext) => void;
  metadataOverrides?: Record<string, unknown>;
  onSubmitStateChange?: (state: 'idle' | 'submitting' | 'complete') => void;
  strokeColor?: string;
  backgroundColor?: string;
  toolMode?: ToolMode;
};

export const DoodleCanvas = forwardRef<DoodleCanvasRef, Props>(function DoodleCanvas(
  {
  lobbyId,
  playerSlot,
  doodleType,
  onResult,
  metadataOverrides,
  onSubmitStateChange,
  strokeColor = '#ffeb3b',
  backgroundColor = '#1f1f1f',
  toolMode = 'pen',
}: Props,
ref: React.ForwardedRef<DoodleCanvasRef>
) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const strokesRef = useRef<Stroke[]>([]);
  const drawingRef = useRef(false);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const [status, setStatus] = useState<string>('Ready to sketch');
  const [currentToolMode, setCurrentToolMode] = useState<ToolMode>(toolMode);

  const resizeCanvas = () => {
    if (!canvasRef.current || !containerRef.current) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const size = Math.min(rect.width, rect.height);
    const dpr = window.devicePixelRatio || 1;
    const displaySize = size;
    const actualSize = Math.floor(displaySize * dpr);
    
    const needsResize = canvas.width !== actualSize || canvas.height !== actualSize;
    
    if (needsResize) {
      const imageData = ctxRef.current && canvas.width > 0 && canvas.height > 0
        ? ctxRef.current.getImageData(0, 0, canvas.width, canvas.height)
        : null;
      
      canvas.width = actualSize;
      canvas.height = actualSize;
      canvas.style.width = `${displaySize}px`;
      canvas.style.height = `${displaySize}px`;
      
      const ctx = canvas.getContext('2d', { willReadFrequently: false });
      if (!ctx) return;
      
      ctx.scale(dpr, dpr);
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.lineWidth = currentToolMode === 'eraser' ? 20 : 4;
      ctx.strokeStyle = currentToolMode === 'eraser' ? backgroundColor : strokeColor;
      ctx.globalCompositeOperation = currentToolMode === 'eraser' ? 'destination-out' : 'source-over';
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, displaySize, displaySize);
      
      if (imageData && imageData.width > 0 && imageData.height > 0) {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = imageData.width;
        tempCanvas.height = imageData.height;
        const tempCtx = tempCanvas.getContext('2d');
        if (tempCtx) {
          tempCtx.putImageData(imageData, 0, 0);
          ctx.drawImage(tempCanvas, 0, 0, displaySize, displaySize);
        }
      }
      
      ctx.beginPath();
      ctxRef.current = ctx;
    } else {
      // Update context settings even if size hasn't changed
      const ctx = ctxRef.current;
      if (ctx) {
        ctx.lineWidth = currentToolMode === 'eraser' ? 20 : 4;
        ctx.strokeStyle = currentToolMode === 'eraser' ? backgroundColor : strokeColor;
        ctx.globalCompositeOperation = currentToolMode === 'eraser' ? 'destination-out' : 'source-over';
      }
    }
  };

  useEffect(() => {
    resizeCanvas();
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    const resizeObserver = new ResizeObserver(() => resizeCanvas());
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
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
      if (ctxRef.current) {
        ctxRef.current.beginPath();
      }
    };

    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [strokeColor, backgroundColor, currentToolMode]);

  useEffect(() => {
    if (toolMode !== currentToolMode) {
      setCurrentToolMode(toolMode);
    }
  }, [toolMode]);

  useEffect(() => {
    const ctx = ctxRef.current;
    if (ctx) {
      ctx.lineWidth = currentToolMode === 'eraser' ? 20 : 4;
      ctx.strokeStyle = currentToolMode === 'eraser' ? backgroundColor : strokeColor;
      ctx.globalCompositeOperation = currentToolMode === 'eraser' ? 'destination-out' : 'source-over';
    }
  }, [currentToolMode, strokeColor, backgroundColor]);

  useEffect(() => {
    if (lobbyId) {
      telemetryPublisher.start(lobbyId);
    }
  }, [lobbyId]);

  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const buildMetadata = useCallback(() => {
    const merged: Record<string, unknown> = { player_slot: playerSlot, ...(metadataOverrides ?? {}) };
    Object.keys(merged).forEach((key) => {
      if (merged[key] === undefined || merged[key] === null) {
        delete merged[key];
      }
    });
    return merged;
  }, [playerSlot, metadataOverrides]);

  const pollInference = useCallback(async (ticketId: string) => {
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
  }, []);

  const clearCanvas = useCallback(() => {
    const ctx = ctxRef.current;
    const canvas = canvasRef.current;
    if (ctx && canvas) {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const displaySize = Math.min(rect.width, rect.height);
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, displaySize, displaySize);
      ctx.strokeStyle = strokeColor;
      ctx.globalCompositeOperation = 'source-over';
      ctx.beginPath();
    }
    strokesRef.current = [];
  }, [backgroundColor, strokeColor]);

  const submitDoodle = useCallback(async () => {
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
      onResult(result, { snapshot, doodleType, slot: playerSlot });
      setStatus('Inference complete');
      onSubmitStateChange?.('complete');
      clearCanvas();
    } catch (error: any) {
      setStatus(error?.message ?? 'Submission failed');
      onSubmitStateChange?.('idle');
    }
  }, [lobbyId, doodleType, playerSlot, metadataOverrides, onSubmitStateChange, onResult, buildMetadata, pollInference, clearCanvas]);

  useImperativeHandle(
    ref,
    () => ({
      submit: submitDoodle,
      clear: clearCanvas,
      getStrokes: () => strokesRef.current,
      getSnapshot: () => canvasRef.current?.toDataURL('image/png') ?? null,
    }),
    [submitDoodle, clearCanvas],
  );

  const toStroke = (event: PointerEvent, canvas: HTMLCanvasElement): Stroke => {
    const rect = canvas.getBoundingClientRect();
    // Since context is already scaled by DPR, we use display coordinates directly
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      pressure: event.pressure,
      timestamp: Date.now(),
    };
  };

  return (
    <div className="doodle-canvas" ref={containerRef}>
      <canvas ref={canvasRef} />
    </div>
  );
});
