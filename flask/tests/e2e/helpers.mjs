export function uniqueGameId(prefix = 'test') {
  return `${prefix}${Date.now()}${Math.floor(Math.random() * 1000)}`;
}

// bootstrap-vue-next keeps modal/offcanvas content mounted in the DOM even while hidden (e.g. the
// "Select player" modal, the Create/Join game-list, the About modal's help text), so a plain
// getByText() match on a player's name routinely resolves to more than one element. The players
// list itself always renders as a BAccordionItem header (.accordion-button), which nothing hidden
// happens to share -- scope to that instead of fighting every possible hidden duplicate.
export function playerListItem(page, name) {
  return page.locator('.accordion-button', { hasText: name });
}

export async function createGame(page, gameId, password = '') {
  await page.goto('/');
  await page.waitForSelector('text=Create / Join', { timeout: 15000 });
  await page.fill('input[placeholder*="Game ID"]', gameId);
  if (password) {
    await page.fill('input[placeholder*="Password"]', password);
  }
  await page.click('button:has-text("CREATE / JOIN")');
  await page.waitForSelector('text=Add player', { timeout: 15000 });
}

export async function addPlayer(page, name, color) {
  await page.click('button:has-text("Add player")');
  await page.waitForSelector('#inputPlayerName', { timeout: 5000 });
  await page.fill('#inputPlayerName', name);
  await page.fill('.modal.show input[type="color"]', color);
  await page.waitForTimeout(200);
  await page.click('.modal.show .btn-primary, .modal.show button:has-text("OK")');
  await page.waitForTimeout(500);
}

// HINT auto-selects a valid set of 3 cards (shown with the "border-warning" class), but
// clicking "SET!" resets that selection first (see TurnControl's "untoggle-request" flow) --
// so the hinted cards have to be re-clicked afterwards to actually mark them for submission.
export async function submitHintedSet(page, playerName) {
  await page.click('button:has-text("HINT")');
  await page.waitForTimeout(1000);
  const hintedCards = await page.evaluate(() =>
    [...document.querySelectorAll('[id^="card-"]')]
      .filter((el) => el.className.includes('border-warning'))
      .map((el) => el.id.replace('card-', ''))
  );

  await page.click('button:has-text("SET!")');
  await page.waitForSelector('text=Select player', { timeout: 5000 }).catch(() => {});
  // Only one human player: no "select player" modal, submission starts immediately.
  if (await page.locator('.modal.show:has-text("Select player")').isVisible().catch(() => false)) {
    await page.waitForTimeout(800); // let the pause-on-SET-click state settle
    await page.click(`.modal.show button:has-text("${playerName}")`);
    await page.waitForSelector('.modal.show', { state: 'hidden', timeout: 5000 }).catch(() => {});
  }
  await page.waitForTimeout(1200); // playerState -> SUBMITTING settle delay

  for (const cardId of hintedCards) {
    await page.click(`#card-${cardId}`);
    await page.waitForTimeout(300);
  }

  return hintedCards;
}
