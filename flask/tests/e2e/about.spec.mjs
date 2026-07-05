import { test, expect } from '@playwright/test';
import { createGame, uniqueGameId } from './helpers.mjs';

test('opens the About/Help modal', async ({ page }) => {
  const gameId = uniqueGameId('about');
  await createGame(page, gameId);

  await page.click('button:has-text("HELP")');
  await expect(page.getByText('pySET QUICK START')).toBeVisible();
});
