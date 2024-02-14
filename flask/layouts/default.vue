<template>

  <BNavbar toggleable="lg" type="light" variant="light">
    <BNavbarBrand href="#"><h1>pySET</h1></BNavbarBrand>
    <BNavbarToggle target="nav-collapse" />

    <BCollapse id="nav-collapse" is-nav>
      <BNavbarNav class="ms-auto mb-2 mb-lg-0">
        <HRControl :gameState="gameState"
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

    <BCardGroup deck class="col-8 pt-2">
      <BCard title="SET">
        <SetGrid :gameState="gameState"
                 :playerState="playerState"

                 :selectedPlayer="selectedPlayer"
                 :playersStats="playersStats"
                 :hintedCards="hintedCards"

                 @update-player-state="updatePlayerStateHandler($event)"
                 @update-game-state="updateGameStateHandler($event)"/>
      </BCard>

      <BCard title="Scores">
        <PlayerCRUD :gameState="gameState"
                    :playerState="playerState"

                    :playersStats="playersStats"

                    @update-player-state="updatePlayerStateHandler($event)"/>

        <div class="mt-3"></div>

        <PlayerScore :gameState="gameState"
                     :playerState="playerState"

                     :playersStats="playersStats"

                     @update-player-state="updatePlayerStateHandler($event)"/>
      </BCard >
    </BCardGroup>

    <div class="bottom">
      <div>
        <span class="badge bg-dark">version</span>
        <span class="badge bg-info">{{ version }}</span>
      </div>
    </div>

  </div>

</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";
import { initConfig, sleep } from "~/assets/helpers.js";
import { getGameState, getPlayersInfos } from "~/assets/webAppAPI.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const version = ref("0.1.0");

const config = ref({});
const _ = useState('config', async () => await initConfig());
config.value = await useState('config').value.then(r => r);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

const gameState = ref(GameStates.NEW.name);
const playerState = ref(PlayerStates.UPDATE.name);

const selectedPlayer = ref('');
const playersStats = ref([{ name: "John",
                            is_ai: false,
                            calls: 0,
                            number_invalid_sets: 0,
                            number_valid_sets: 0,
                            valid_sets: [],
                            average_answers_time: 0,
                            answers_time: [] }]);

const hintedCards = ref([]);

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => {
  console.log(config.value);
});

onMounted(async () => {
  try {
    if(config.value.version) {
      version.value = config.value.version;
    }
    else {
      throw new Error('Version is undefined');
    }
  }
  catch (error) {
    version.value = 'Undefined';
    console.log(`Could not retrieve pySET version from config: ${error}`);
  }

  const respGame = await getCurrentGameState();
  gameState.value = respGame.gameState;

  const respPlayers = await getCurrentPlayersStats();
  playerState.value = respPlayers.status ? PlayerStates.IDLE.name : PlayerStates.LOCKED.name;
  playersStats.value = respPlayers.playersStats;
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
    selectedPlayer.value = '';
    return { status: true };
  }
  else if (ev.playerState == PlayerStates.SUBMITTING.name) {
    selectedPlayer.value = ev.data.playerName;
  }
  else {
    await sleep(300); // Mandatory to avoid VUE crashes
  }

  playerState.value = ev.playerState;
  return { status: true };
};

const updateGameStateHandler = async (ev) => {
  console.log(`default -- New signal from: ${ev.from} for: ${ev.typeState} requesting state: ${ev.gameState}`);

  if (ev.data.action == 'hint') {
    hintedCards.value = ev.data.hintedCards;
    return { status: true };
  }

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

const getCurrentGameState = async () => {
  const resp = await getGameState(modalGenericMessage);
  if (!resp.status) {
    return { status: resp.status, gameState: GameStates.UNDEFINED.name };
  }
  return { status: true, gameState: GameStates[resp.content.game_state].name };
};

const getCurrentPlayersStats = async () => {
  const resp = await getPlayersInfos(modalGenericMessage);
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