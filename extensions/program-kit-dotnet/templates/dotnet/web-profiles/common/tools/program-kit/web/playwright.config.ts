import { defineConfig } from '@playwright/test';

// Pinned Playwright supports this artifact control; traces/screenshots alone
// do not prevent automatic failure DOM snapshots (playwright/lib/index.js).
process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';

export default defineConfig({
  testDir: './tests',
  forbidOnly: true,
  retries: process.env.CI ? 2 : 0,
  reporter: [['./private-diagnostics.mjs', { outputFile: 'private-results.json' }]],
  use: {
    baseURL: process.env.PROGRAMKIT_BASE_URL ?? 'http://localhost:5000',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
