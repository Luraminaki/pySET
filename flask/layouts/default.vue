<template>

  <BNavbar toggleable="lg" type="light" variant="light">
    <BNavbarBrand href="#"><h1>pySET</h1></BNavbarBrand>
    <BNavbarNav>
      <BNavItem>GAME ID: {{ gameID }}</BNavItem>
    </BNavbarNav>
    <BNavbarToggle target="nav-collapse" />

    <BCollapse id="nav-collapse" is-nav>
      <BNavbarNav class="ms-auto mb-2 mb-lg-0">
        <HRControl :gameAuth="{ gameID: gameID, gameSecret: gameSecret }"
                   :gameState="gameState"
                   :playerState="playerState"

                   @update-player-state="updatePlayerStateHandler($event)"
                   @update-game-state="updateGameStateHandler($event)"/>
      </BNavbarNav>
    </BCollapse>
  </BNavbar>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage"
                         @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

  <div class="mt-2 is-center">

    <b-modal v-model="firstLaunch" title="Create / Join" @hide.prevent hide-footer>
      <b-accordion>
        <b-accordion-item title="NEW" visible>
          <BFormInput v-model="gameID" :state="validGameID" type="text" :placeholder="`Game ID (${minIDLength} characters minimum)`"/>
          <BFormInput class="mt-1" v-model="gameSecret" type="password" :placeholder="`Password (Leave empty if free to join)`"/>
          <BButton class="mt-2" pill :disabled="!validGameID" @click="gameCreateJoin(gameID, gameSecret)">
            CREATE / JOIN
          </BButton>
        </b-accordion-item>
        <b-accordion-item v-for="game in games" :key="game.game_id" :title="String(game.has_secret ? '🔒' : '') + game.game_id">
          <BFormInput v-model="gameSecret" v-if="game.has_secret" type="password" :placeholder="`Password`"/>
          <BButton class="mt-2" pill :disabled="game.has_secret && String(gameSecret) == ''" @click="gameCreateJoin(game.game_id, String(game.has_secret ? gameSecret : ''))">
            JOIN
          </BButton>
        </b-accordion-item>
      </b-accordion>
    </b-modal>

    <SetGame v-if="!firstLaunch"
             :gameAuth="{ gameID: gameID, gameSecret: gameSecret }"
             :gameState="gameState"
             :playerState="playerState"

             :playersStats="playersStats" 

             @update-player-state="updatePlayerStateHandler($event)"
             @update-game-state="updateGameStateHandler($event)"/>

    <div class="bottom">
      <div>
        <span class="badge bg-dark">version</span>
        <span class="badge bg-info">{{ version }}</span>
      </div>

      <div>
        <span class="badge bg-dark">games</span>
        <span :class="games.length < maxGames ? 'badge bg-success' : 'badge bg-danger'">{{ games.length }} / {{ maxGames }}</span>
      </div>
    </div>

  </div>

</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";
import { initConfig, sleep } from "~/assets/helpers.js";
import { initSetGame, getRunningGames, getGameState, getPlayersInfos } from "~/assets/webAppAPI.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const version = ref("0.1.0");

const config = ref({});
const _ = useState('config', async () => await initConfig());
config.value = await useState('config').value.then(r => r);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

const games = ref([]);
const maxGames = ref(10);

const minIDLength = ref(3)
const gameID = ref('');
const validGameID = computed(() => (gameID.value.length >= minIDLength.value && gameID.value.length <= 36));
const gameSecret = ref('');
const firstLaunch = ref(true);

const gameState = ref(GameStates.NEW.name);
const playerState = ref(PlayerStates.UPDATE.name);

const playersStats = ref([{ name: "John",
                            is_ai: false,
                            calls: 0,
                            number_invalid_sets: 0,
                            number_valid_sets: 0,
                            valid_sets: [],
                            average_answers_time: 0,
                            answers_time: [] }]);

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => {
  console.log(config.value);
});

onMounted(async () => {
  await checkBackend();
});

// ###################
// ######  GUI  ######
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

// ###################
// #####  FUNCS  #####
// ###################

const updatePlayerStateHandler = async (ev) => {
  console.log(`default -- New signal from: ${ev.from} for: ${ev.typeState} requesting state: ${ev.playerState}`);

  if (ev.playerState == PlayerStates.UPDATE.name) {
    const resp = await getCurrentPlayersStats()
    playerState.value = resp.status ? PlayerStates.IDLE.name : PlayerStates.LOCKED.name;
    playersStats.value = resp.playersStats;
    return { status: true };
  }
  else {
    await sleep(300); // Mandatory to avoid VUE crashes
  }

  playerState.value = ev.playerState;
  return { status: true };
};

const updateGameStateHandler = async (ev) => {
  console.log(`default -- New signal from: ${ev.from} for: ${ev.typeState} requesting state: ${ev.gameState}`);

  if (ev.gameState == GameStates.ENDED.name) {
    modalGenericMessage.value.modalTitle = 'Game Over';
    modalGenericMessage.value.modalMessage = 'No SET left to be found. Press RESET to play again.';
    modalGenericMessage.value.triggerModal = true;
  }
  else {
    await sleep(300); // Mandatory to avoid VUE crashes
  }

  gameState.value = ev.gameState;
  return { status: true };
};

// ###################
// ###  WebAppAPI  ###
// ###################

const checkBackend = async () => {
  try {
    if(config.value.version) {
      version.value = config.value.version;
      maxGames.value = config.value.MAX_SESSIONS;
    }
    else {
      throw new Error('Version is undefined');
    }
  }
  catch (error) {
    version.value = 'Undefined';
    console.log(`Could not retrieve pySET version from config: ${error}`);
    return { status: false };
  }

  const resp = await getRunningGames(modalGenericMessage);
  if (!resp.status){
    return { status: false };
  }

  games.value = resp.content.games;
};

const gameCreateJoin = async (formGameID, formGameSecret) => {
  gameID.value = formGameID;
  gameSecret.value = formGameSecret;

  const respInit = await initSetGame(modalGenericMessage, { gameID: gameID.value, gameSecret: gameSecret.value });
  if (!respInit.status){
    firstLaunch.value = true;
    gameID.value = '';
    gameSecret.value = '';
    return { status: false };
  }

  const respGame = await getStatesAndStats();
  if (!respGame.status){
    firstLaunch.value = true;
    gameID.value = '';
    gameSecret.value = '';
    return { status: false };
  }

  firstLaunch.value = false;

  const resp = await getRunningGames(modalGenericMessage);
  if (!resp.status){
    return { status: false };
  }

  games.value = resp.content.games;

};

const getStatesAndStats = async () => {
  const respGame = await getCurrentGameState();
  gameState.value = respGame.gameState;

  const respPlayers = await getCurrentPlayersStats();
  playerState.value = respPlayers.status ? PlayerStates.IDLE.name : PlayerStates.LOCKED.name;
  playersStats.value = respPlayers.playersStats;

  return { status: respGame.status && respPlayers.status }
};

const getCurrentGameState = async () => {
  const resp = await getGameState(modalGenericMessage, { gameID: gameID.value, gameSecret: gameSecret.value });
  if (!resp.status) {
    return { status: resp.status, gameState: GameStates.UNDEFINED.name };
  }
  return { status: true, gameState: GameStates[resp.content.game_state].name };
};

const getCurrentPlayersStats = async () => {
  const resp = await getPlayersInfos(modalGenericMessage, { gameID: gameID.value, gameSecret: gameSecret.value });
  if (!resp.status) {
    return { status: resp.status, playersStats: [] };
  }
  return { status: true, playersStats: resp.content.players_stats };
};
</script>

<style scoped>
.is-center {
  display: flex;
  justify-content: center;
  align-content: center;
}
.bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100vw;
  display: flex !important;
  flex-direction: row;
  justify-content: space-between;
}
</style>