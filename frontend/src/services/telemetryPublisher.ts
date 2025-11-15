import { apiClient } from '@/services/apiClient';

export class TelemetryPublisher {
  private fpsSamples: number[] = [];
  private latencySamples: number[] = [];
  private observer?: PerformanceObserver;

  start(sessionId: string) {
    if (typeof window === 'undefined') return;
    this.observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      for (const entry of entries) {
        if (entry.duration) {
          this.latencySamples.push(entry.duration);
        }
      }
    });
    this.observer.observe({ entryTypes: ['event', 'measure'] });

    const loop = () => {
      const now = performance.now();
      if (this.fpsSamples.length > 100) this.fpsSamples.shift();
      this.fpsSamples.push(now);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);

    window.addEventListener('beforeunload', () => {
      this.flush(sessionId).catch(() => undefined);
    });
  }

  async flush(sessionId: string) {
    if (!this.latencySamples.length) return;
    const samples = this.latencySamples.slice(-50);
    this.latencySamples = [];
    await apiClient.publishTelemetry({
      lobby_id: sessionId,
      type: 'canvas_latency',
      samples,
    });
  }
}

export const telemetryPublisher = new TelemetryPublisher();
