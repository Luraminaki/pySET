import {
  initSetGame,
  getRunningGames,
  changeGameState as changeGameStateApi,
  getGameState,
  getGame,
  resetGame as resetGameApi,
  submitSet as submitSetApi,
  sendPenalty,
  getHints,
  getPlayersInfos,
  removePlayer as removePlayerApi,
  addPlayer as addPlayerApi,
} from '~/assets/webAppAPI.js';
import { initConfig } from '~/assets/helpers.js';
import { GameStates, PlayerStates } from '~/assets/states.js';

export const useGameStore = defineStore('game', () => {
  // ##################
  // #####  APP   #####
  // ##################

  const version = ref('0.1.0');
  const config = ref({});

  const modalGenericMessage = ref({ triggerModal: false, modalTitle: '', modalMessage: '' });

  function showMessage(title, message) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: title, modalMessage: message };
  }

  function clearMessage() {
    modalGenericMessage.value = { triggerModal: false, modalTitle: '', modalMessage: '' };
  }

  const THEME_STORAGE_KEY = 'pyset-theme';
  const theme = ref('light');

  function applyTheme(newTheme) {
    theme.value = newTheme;
    document.documentElement.setAttribute('data-bs-theme', newTheme);
  }

  // Defaults to the OS/browser preference. Until the user explicitly toggles (see toggleTheme),
  // no choice is stored, so the app keeps following the system preference live -- e.g. the OS
  // switching to dark mode at sunset -- rather than freezing on whatever it resolved to at load.
  function initTheme() {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored) {
      applyTheme(stored);
      return;
    }

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    applyTheme(media.matches ? 'dark' : 'light');
    media.addEventListener('change', (event) => {
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        applyTheme(event.matches ? 'dark' : 'light');
      }
    });
  }

  function toggleTheme() {
    const newTheme = theme.value == 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
  }

  const games = ref([]);
  const maxGames = ref(10);

  async function loadConfig() {
    config.value = await initConfig();
  }

  async function checkBackend() {
    if (!config.value.version) {
      version.value = 'Undefined';
      console.error('Could not retrieve pySET version from config: version is undefined');
      return { status: false };
    }

    version.value = config.value.version;
    maxGames.value = config.value.MAX_SESSIONS;

    const resp = await getRunningGames(modalGenericMessage);
    if (!resp.status) {
      return { status: false };
    }

    games.value = resp.content.games;
    return { status: true };
  }

  // ##################
  // #####  GAME  #####
  // ##################

  const minIDLength = ref(3);
  const gameID = ref('');
  const gameSecret = ref('');
  const gameAuth = computed(() => ({ gameID: gameID.value, gameSecret: gameSecret.value }));
  const validGameID = computed(() => (gameID.value.length >= minIDLength.value && gameID.value.length <= 36));

  const firstLaunch = ref(true);

  const gameState = ref(GameStates.NEW.name);
  const playerState = ref(PlayerStates.UPDATE.name);
  const playersStats = ref([]);

  const grid = ref([[]]);
  const drawPile = ref(0);
  const hintsRequested = ref(0);
  const validAmountSelectedCards = computed(() => (grid.value[0].length));

  // Signals a "hint" (highlight these cards) or "untoggle-request" (deselect everything) to
  // every SetCard -- consumed the same way the old cardsEvent prop was.
  const cardsEvent = ref({ cards: [], event: '' });
  const resetToggleCounter = ref(0);
  const selectedCards = ref([]);

  const selectedPlayer = ref('');
  const penalisedPlayer = ref('');

  async function getCurrentGameState() {
    const resp = await getGameState(modalGenericMessage, gameAuth.value);
    if (!resp.status) {
      return { status: resp.status, gameState: GameStates.UNDEFINED.name };
    }
    return { status: true, gameState: GameStates[resp.content.game_state].name };
  }

  async function refreshPlayersStats() {
    const resp = await getPlayersInfos(modalGenericMessage, gameAuth.value);
    if (!resp.status) {
      playerState.value = PlayerStates.LOCKED.name;
      playersStats.value = [];
      return { status: false };
    }
    playerState.value = PlayerStates.IDLE.name;
    playersStats.value = resp.content.players_stats;
    return { status: true };
  }

  // Mirrors the previous "bubble an update-player-state/update-game-state event up to whoever
  // owns the state" handlers: UPDATE means "go refresh from the backend", anything else is a
  // direct assignment. The old handlers each did `await sleep(300)` here ("Mandatory to avoid
  // VUE crashes") -- that guarded against races in the old 3-4-level prop-drilling + bubbled-
  // watcher architecture, which no longer exists now that everything reads/writes the store
  // directly. Manually exercised the "quick double penalty" / "fast submit" sequences the delay
  // used to paper over (dev server and a production build) with no console/Vue errors, but this
  // isn't backed by a committed regression test -- worth adding one if this ever regresses.
  async function setPlayerState(newPlayerState) {
    if (newPlayerState == PlayerStates.UPDATE.name) {
      await refreshPlayersStats();
      return;
    }
    playerState.value = newPlayerState;
  }

  async function setGameState(newGameState) {
    if (newGameState == GameStates.ENDED.name) {
      showMessage('Game Over', 'No SET left to be found. Press RESET to play again.');
    }
    gameState.value = newGameState;
  }

  // Previously a watch on the gameState *prop* inside SetGrid.vue -- RESET/UPDATE are signal
  // values (not just display state), meaning "go reload the grid from the backend". Centralized
  // here since grid/drawPile are now store state rather than something only SetGrid owned.
  watch(gameState, async (newValue) => {
    if (newValue == GameStates.RESET.name) {
      await loadGame(true);
    }
    else if (newValue == GameStates.UPDATE.name) {
      await loadGame(false);
    }
  });

  async function createOrJoinGame(formGameID, formGameSecret) {
    gameID.value = formGameID;
    gameSecret.value = formGameSecret;

    const respInit = await initSetGame(modalGenericMessage, { ...gameAuth.value });
    if (!respInit.status) {
      firstLaunch.value = true;
      gameID.value = '';
      gameSecret.value = '';
      return { status: false };
    }

    const respGameState = await getCurrentGameState();
    gameState.value = respGameState.gameState;
    const respStats = await refreshPlayersStats();

    if (!respGameState.status || !respStats.status) {
      firstLaunch.value = true;
      gameID.value = '';
      gameSecret.value = '';
      return { status: false };
    }

    firstLaunch.value = false;

    const resp = await getRunningGames(modalGenericMessage);
    if (!resp.status) {
      return { status: false };
    }

    games.value = resp.content.games;
    return { status: true };
  }

  async function addPlayer(name, color) {
    const resp = await addPlayerApi(modalGenericMessage, { ...gameAuth.value, name, color });
    if (!resp.status) {
      return { status: false };
    }
    await setPlayerState(PlayerStates.UPDATE.name);
    return { status: true };
  }

  async function removePlayer(name) {
    const resp = await removePlayerApi(modalGenericMessage, { ...gameAuth.value, name });
    if (!resp.status) {
      return { status: false };
    }
    await setPlayerState(PlayerStates.UPDATE.name);
    return { status: true };
  }

  async function loadGame(reload = false) {
    cardsEvent.value.cards = [];

    penalisedPlayer.value = '';
    selectedCards.value = [];

    if (reload) {
      hintsRequested.value = 0;
      grid.value = [[]];
      drawPile.value = 0;
    }

    const resp = await getGame(modalGenericMessage, { ...gameAuth.value });
    if (!resp.status) {
      await setGameState(GameStates.UNDEFINED.name);
      return { status: false };
    }

    grid.value = resp.content.grid;
    drawPile.value = resp.content.draw_pile;
    await setGameState(GameStates[resp.content.game_state].name);

    return { status: true };
  }

  async function startOrPauseGame() {
    const enablePause = gameState.value == GameStates.RUNNING.name;
    const resp = await changeGameStateApi(modalGenericMessage, { ...gameAuth.value, enablePause });
    if (!resp.status) {
      return { status: false };
    }
    await setGameState(GameStates[resp.content.game_state].name);
    return { status: true };
  }

  async function resetGame(hard) {
    const resp = await resetGameApi(modalGenericMessage, { ...gameAuth.value, hard });
    if (!resp.status) {
      return { status: false };
    }
    await setGameState(GameStates.RESET.name);
    await setPlayerState(PlayerStates.UPDATE.name);
    return { status: true };
  }

  async function requestHint() {
    const resp = await getHints(modalGenericMessage, { ...gameAuth.value });
    if (!resp.status) {
      return { status: false };
    }

    const random = Math.floor(Math.random() * resp.content.sets.length);
    const newHintedCards = resp.content.sets[random];

    cardsEvent.value.cards = [...newHintedCards];
    cardsEvent.value.event = 'hint';
    hintsRequested.value = hintsRequested.value + 1;

    return { status: true };
  }

  // Deselects every card (fires before showing the "pick a player"/submitting flow), mirroring
  // the previous 'untoggle-request' signal. Each SetCard reports back via toggleCard() below,
  // which is what actually clears cardsEvent once every card has responded.
  function untoggleAllCards() {
    cardsEvent.value.event = 'untoggle-request';
  }

  function checkResetCount() {
    const cards = grid.value.flat();
    if (cards.length != 0 && cards.length == resetToggleCounter.value) {
      cardsEvent.value.event = '';
      cardsEvent.value.cards = [];
      resetToggleCounter.value = 0;
    }
  }

  function toggleCard(card, action) {
    if (action == 'remove') {
      const index = selectedCards.value.indexOf(card);
      if (index > -1) {
        selectedCards.value.splice(index, 1);
      }
    }
    else if (action == 'add') {
      if (selectedCards.value.length < 3) {
        selectedCards.value.push(card);
      }
    }

    if (cardsEvent.value.event == 'untoggle-request') {
      resetToggleCounter.value = resetToggleCounter.value + 1;
      checkResetCount();
    }
  }

  // Called for the player picked to submit (either the sole human player, auto-selected, or
  // whoever was clicked in the "select player" modal) -- resumes a paused game first if needed.
  async function proceedWithSelectedPlayer(playerName) {
    if (gameState.value == GameStates.PAUSED.name) {
      const resp = await startOrPauseGame();
      if (!resp.status) {
        selectedPlayer.value = '';
        return { status: false };
      }
    }

    selectedPlayer.value = playerName;
    await setPlayerState(PlayerStates.SUBMITTING.name);

    return { status: true };
  }

  async function submitSet(playerName, cards) {
    untoggleAllCards();

    const resp = await submitSetApi(modalGenericMessage, { ...gameAuth.value, playerName, set: cards });

    selectedPlayer.value = '';

    if (!resp.status) {
      if (resp.content.error == 'CARDS_NOT_FOUND') {
        await setGameState(GameStates.UPDATE.name);
      }
      await setPlayerState(PlayerStates.UPDATE.name);
      return { status: false };
    }

    await setGameState(GameStates.UPDATE.name);

    if (resp.content.is_valid) {
      await setPlayerState(PlayerStates.UPDATE.name);
    }
    else {
      // Mechanically valid submission, wrong cards -- penalize instead of just refreshing.
      penalisedPlayer.value = playerName;
    }

    return { status: true };
  }

  // Called by Timers.vue once it reacts to penalisedPlayer becoming non-empty. Returns the
  // player's index so the caller can drive its own (purely presentational) progress bar.
  async function requestPenalty(playerName) {
    const playerIndex = playersStats.value.findIndex((player) => player.name == playerName);
    if (playerIndex == -1) {
      showMessage('Not found', `Player ${playerName} not found`);
      return { status: false, playerIndex: -1 };
    }

    untoggleAllCards();

    const resp = await sendPenalty(modalGenericMessage, { ...gameAuth.value, playerName });
    if (!resp.status) {
      return { status: false, playerIndex: -1 };
    }

    // TODO: Use a toast here
    showMessage('Applying penalty', `${config.value.PENALTY_TIMEOUT_SECONDS}s penalty applied to ${playerName}`);
    await setPlayerState(PlayerStates.UPDATE.name);

    return { status: true, playerIndex };
  }

  return {
    version,
    config,
    modalGenericMessage,
    showMessage,
    clearMessage,
    theme,
    initTheme,
    toggleTheme,
    games,
    maxGames,
    loadConfig,
    checkBackend,

    minIDLength,
    gameID,
    gameSecret,
    gameAuth,
    validGameID,
    firstLaunch,
    gameState,
    playerState,
    playersStats,
    grid,
    drawPile,
    hintsRequested,
    validAmountSelectedCards,
    cardsEvent,
    selectedCards,
    selectedPlayer,
    penalisedPlayer,

    createOrJoinGame,
    addPlayer,
    removePlayer,
    loadGame,
    startOrPauseGame,
    resetGame,
    requestHint,
    untoggleAllCards,
    toggleCard,
    proceedWithSelectedPlayer,
    submitSet,
    requestPenalty,
  };
});
