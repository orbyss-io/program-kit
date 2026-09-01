import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  forbidOnly: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.PROGRAMKIT_BASE_URL ?? 'http://localhost:5000',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
