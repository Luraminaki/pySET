import { test, expect } from '@playwright/test';
import { createGame, addPlayer, uniqueGameId, playerListItem } from './helpers.mjs';

test('submitting an invalid set applies a penalty', async ({ page }) => {
  const gameId = uniqueGameId('penalty');
  await createGame(page, gameId);
  await addPlayer(page, 'Eve', '#123456');

  await page.click('button:has-text("START")');
  await page.click('button:has-text("SET!")');
  await page.waitForTimeout(1200); // playerState -> SUBMITTING settle delay (single player, no select-player modal)

  // Three arbitrary cards are overwhelmingly likely to not form a valid SET.
  const cardIds = await page.evaluate(() =>
    [...document.querySelectorAll('[id^="card-"]')].slice(0, 3).map((el) => el.id.replace('card-', ''))
  );
  for (const cardId of cardIds) {
    await page.click(`#card-${cardId}`);
    await page.waitForTimeout(200);
  }

  await page.click('button:has-text("Submit SET")');
  // The dynamic notification text ("<N>s penalty applied to <player>") is specific enough that it
  // can't collide with the static "Penalty time" label or the About modal's help text.
  await expect(page.getByText(/penalty applied to/i)).toBeVisible();
});

test('hard reset clears players', async ({ page }) => {
  const gameId = uniqueGameId('hardreset');
  await createGame(page, gameId);
  await addPlayer(page, 'Frank', '#abcdef');
  await expect(playerListItem(page, 'Frank')).toBeVisible();

  // RESET is disabled while the game is still in its unstarted "NEW" state (nothing to reset yet).
  await page.click('button:has-text("START")');
  await expect(page.locator('button:has-text("PAUSE")')).toBeVisible();

  await page.click('button:has-text("RESET")');
  await page.waitForSelector('text=Reset game?');
  await page.click('.modal.show button:has-text("HARD")');

  await expect(page.locator('button:has-text("Add player")')).toBeVisible();
  await expect(playerListItem(page, 'Frank')).toHaveCount(0);
});
