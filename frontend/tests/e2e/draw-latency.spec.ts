import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000';

async function measureFrameLatency(page) {
  return await page.evaluate(async () => {
    return await new Promise<number>((resolve) => {
      const samples: number[] = [];
      let last = performance.now();
      function frame(now: number) {
        samples.push(now - last);
        last = now;
        if (samples.length > 60) {
          resolve(samples.sort()[Math.floor(samples.length * 0.95)]);
          return;
        }
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
  });
}

test('canvas loop maintains <=50ms latency budget', async ({ page }) => {
  await page.goto(`${FRONTEND_URL}/match`);
  await expect(page.getByRole('heading', { name: /Lobby/ })).toBeVisible();
  const latency = await measureFrameLatency(page);
  expect(latency).toBeLessThanOrEqual(50);
});
