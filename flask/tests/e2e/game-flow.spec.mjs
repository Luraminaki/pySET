import { test, expect } from '@playwright/test';
import { createGame, addPlayer, submitHintedSet, uniqueGameId, playerListItem } from './helpers.mjs';

test('create game, add players, start, submit a valid hinted set, view history, soft reset', async ({ page }) => {
  const gameId = uniqueGameId('golden');
  await createGame(page, gameId);

  await addPlayer(page, 'Alice', '#ff0000');
  await addPlayer(page, 'Bob', '#00ff00');
  await expect(playerListItem(page, 'Alice')).toBeVisible();
  await expect(playerListItem(page, 'Bob')).toBeVisible();

  await page.click('button:has-text("START")');
  await expect(page.locator('button:has-text("PAUSE")')).toBeVisible();
  await expect(page.getByText('Drawing pile: 69 cards')).toBeVisible();

  await submitHintedSet(page, 'Alice');
  await page.click('button:has-text("Submit SET")');

  await expect(page.getByText('Drawing pile: 66 cards')).toBeVisible();

  // Score history offcanvas for the player who just scored (also exercises the fix for
  // duplicate DOM ids between the live grid and the history cards -- see ScoreDetails.vue).
  await page.click('button:has-text("Alice")');
  await page.click('button:has-text("SHOW HISTORY")');
  await expect(page.getByText(/SET n° 1/)).toBeVisible();
  await page.click('.offcanvas.show .btn-close');

  await page.click('button:has-text("RESET")');
  await page.waitForSelector('text=Reset game?');
  await page.click('.modal.show button:has-text("SOFT")');

  await expect(page.getByText('Drawing pile: 69 cards')).toBeVisible();
  await expect(playerListItem(page, 'Alice')).toBeVisible();
  await expect(playerListItem(page, 'Bob')).toBeVisible();
});
