import { defineConfig } from '@playwright/test';

const pythonBin = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  // The store chains several sleep(300)-guarded state transitions per user action (see
  // stores/game.js), each with its own network round-trip -- a single "click SET!, pick a
  // player, submit" sequence can take several seconds of real wall-clock time. Playwright's
  // 5s default assertion timeout is occasionally too tight for the assertion right after such
  // a chain, even though the app itself is behaving correctly. 10s gives enough margin.
  expect: {
    timeout: 10000,
  },
  // The backend is one shared, stateful process for the whole run (in-memory game sessions) --
  // running tests serially keeps that simple instead of chasing cross-test interference.
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      // Runs against config.test.json (MAX_SESSIONS raised well above the real config's 5) so a
      // full test run never hits the session cap. reuseExistingServer is deliberately off here:
      // silently reusing a real dev backend (config.json, MAX_SESSIONS=5) would misconfigure the
      // whole suite without any visible error.
      command: `"${pythonBin}" -m pyset.server_app -c config.test.json`,
      cwd: '..',
      url: 'http://localhost:10000/api/app/get_config/',
      reuseExistingServer: false,
      timeout: 15000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
  ],
});
