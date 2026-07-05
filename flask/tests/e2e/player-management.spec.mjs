import { test, expect } from '@playwright/test';
import { createGame, addPlayer, uniqueGameId, playerListItem } from './helpers.mjs';

test('joins a password-protected game', async ({ page }) => {
  const gameId = uniqueGameId('pwtest');
  await createGame(page, gameId, 'secret123');

  await expect(page.locator('button:has-text("Add player")')).toBeVisible();
});

test('adds and removes a player', async ({ page }) => {
  const gameId = uniqueGameId('playermgmt');
  await createGame(page, gameId);

  await addPlayer(page, 'Carol', '#ff00ff');
  await addPlayer(page, 'Dave', '#00ffff');
  await expect(playerListItem(page, 'Carol')).toBeVisible();
  await expect(playerListItem(page, 'Dave')).toBeVisible();

  await page.click('button:has-text("Carol")');
  await page.click('button:has-text("DELETE PLAYER")');
  await page.waitForSelector('text=Remove player Carol');
  await page.click('.modal.show button:has-text("OK")');

  await expect(playerListItem(page, 'Carol')).toHaveCount(0);
  await expect(playerListItem(page, 'Dave')).toBeVisible();
});
