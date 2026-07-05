<template>

  <div class="mt-4 is-flex">
    <BButton :variant="buttonGameStateFlavor.variant" @click="changeGameStateRequest()" :disabled="!canToggleGameState">{{ buttonGameStateFlavor.text }}</BButton>
    <BButton :variant="setCalled ? (canSendSet? 'success' : 'outline-success') : 'info'"
             @click="setCalled ? sendSelection(store.selectedPlayer) : selectSubmittingPlayer()"
             :disabled="setCalled ? !canSendSet : !canCallSet">{{ setCalled ? 'Submit SET' : 'SET!' }}</BButton>
    <BButton variant="outline-primary"
             @click="getRandomHint()"
             :disabled="disableHint">HINT</BButton>
  </div>

  <p v-if="store.playersStats.length == 0" style="color: red; font-size: 0.63rem; margin-bottom: 0px; margin-top: 0px">Add at least one player to start</p>

  <b-modal v-model="modalSelectPlayer.do" :title="modalSelectPlayer.modalTitle" no-close-on-backdrop no-close-on-esc no-footer>
    <div class="is-flex">
      <BButton pill v-for="player in humanPlayers" :key="player.name" @click="onPlayerPicked(player.name)">
        {{ player.name }}
      </BButton>
    </div>
  </b-modal>

</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useGameStore } from "~/stores/game.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

const modalSelectPlayer = ref({ do: false, modalTitle: 'Select player', modalMessage: '' });

// Control variables
const canToggleGameState = computed(() => (store.playerState == PlayerStates.IDLE.name &&
                                           (store.gameState == GameStates.NEW.name ||
                                            store.gameState == GameStates.RUNNING.name ||
                                            store.gameState == GameStates.PAUSED.name) &&
                                           store.playersStats.length != 0));
const disableHint = computed(() => (store.gameState != GameStates.RUNNING.name ||
                                    store.playerState == PlayerStates.SUBMITTING.name ||
                                    store.playerState == PlayerStates.LOCKED.name))
const canCallSet = computed(() => (store.playerState == PlayerStates.IDLE.name &&
                                   store.gameState == GameStates.RUNNING.name &&
                                   store.playersStats.length != 0));
const canSendSet = computed(() => (store.playerState == PlayerStates.SUBMITTING.name &&
                                   store.gameState == GameStates.RUNNING.name &&
                                   store.playersStats.length != 0 &&
                                   store.selectedCards.length == store.validAmountSelectedCards));

const setCalled = ref(false);

// Start - Pause button cosmetic changes
const buttonGameStateFlavor = computed(() => {
  const flavor = {variant: 'secondary', text: 'LOCKED'};
  switch(store.gameState) {
    case GameStates.RUNNING.name:
      flavor.variant = 'warning'; flavor.text = 'PAUSE';
      break;
    case GameStates.PAUSED.name:
      flavor.variant = 'success'; flavor.text = 'RESUME';
      break;
    case GameStates.NEW.name:
      flavor.variant = 'success'; flavor.text = 'START';
      break;
    default:
      break;
  }
  return flavor;
});

const humanPlayers = computed(() => store.playersStats.filter(playersStats => !playersStats.is_ai));

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => store.playerState, async (newValue, oldValue) => {
    if (newValue != PlayerStates.SUBMITTING.name && oldValue == PlayerStates.SUBMITTING.name) {
      setCalled.value = false;
    }
  }
);

// ###################
// #####  FUNCS  #####
// ###################

const selectSubmittingPlayer = async () => {
  store.untoggleAllCards();

  if (humanPlayers.value.length == 1) {
    await onPlayerPicked(humanPlayers.value[0].name);
    return;
  }

  if (store.gameState == GameStates.RUNNING.name) {
    const resp = await store.startOrPauseGame();
    if (!resp.status) {
      return;
    }
  }

  modalSelectPlayer.value.do = true;
};

const onPlayerPicked = async (playerName) => {
  modalSelectPlayer.value.do = false;

  const resp = await store.proceedWithSelectedPlayer(playerName);
  if (!resp.status) {
    return;
  }

  setCalled.value = true;
};

// ###################
// ###  WebAppAPI  ###
// ###################

const changeGameStateRequest = async () => {
  await store.startOrPauseGame();
};

const getRandomHint = async () => {
  await store.requestHint();
};

const sendSelection = async (playerName) => {
  await store.submitSet(playerName, store.selectedCards);

  setCalled.value = false;
};
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
}

.btn {
  width: 30% !important;
}
</style>
