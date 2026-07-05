<template>

  <div class="is-flex">
    <BButton variant="success" @click="prepareAdd()" :disabled="disableAdd">
      <i class="mdi mdi-plus-circle-outline"></i>
      Add player
    </BButton>
  </div>

  <b-modal v-model="modalPlayerUpdate.do"
           :title="modalPlayerUpdate.modalTitle"
           :ok-disabled="!validPlayer"
           @ok="updatePlayersStats()"
           @cancel="modalPlayerUpdate.do = false; playerName = ''; playerColor = '#000000'"
           @close="modalPlayerUpdate.do = false">
    <div class="is-flex">
      <BFormInput v-model="playerName" :state="validPlayerName && uniquePlayerName" type="text" :placeholder="`Player name (${minNameLength} characters minimum)`" id="inputPlayerName"/>
      <BFormInput v-model="playerColor" :state="validPlayerColor && uniquePlayerColor" type="color"/>
    </div>
  </b-modal>

</template>

<script setup>
import { ref, computed, watch } from "vue";
import { sleep } from "~/assets/helpers.js";
import { useGameStore } from "~/stores/game.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

const modalPlayerUpdate = ref({ do: false, modalTitle: '', modalMessage: '', action: '', player: { name: '' } });

const disableAdd = computed(() => (store.playersStats.length == store.config.MAX_PLAYERS ||
                                   store.gameState != GameStates.NEW.name ||
                                   store.playerState == PlayerStates.LOCKED.name));

const playerColor = ref('#000000');
const uniquePlayerColor = computed(() => (store.playersStats.filter(findPlayerByColor).length == 0));
const validPlayerColor = computed(() => (playerColor.value != ''));

const minNameLength = ref(3);
const playerName = ref('');
const uniquePlayerName = computed(() => (store.playersStats.filter(findPlayerByName).length == 0));
const validPlayerName = computed(() => (playerName.value.length >= minNameLength.value && playerName.value.length <= store.config.PLAYER_NAME_MAX_CHARS));

const validPlayer = computed(() => (validPlayerName.value && uniquePlayerName.value &&
                                    validPlayerColor.value && uniquePlayerColor.value))

function findPlayerByName(player, index) {
  return player.name == playerName.value;
}

function findPlayerByColor(player, index) {
  return player.color == playerColor.value;
}

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => modalPlayerUpdate.value.do, async (newValue, oldValue) => {
    if (newValue) {
      await sleep(300); // Not optimal, but to reliably autofocus the input form, you have to wait for it...

      const element = document.getElementById('inputPlayerName');
      if (element) {
        element.focus();
      }
    }
  }
);

// ###################
// #####  FUNCS  #####
// ###################

const resetValues = () => {
  playerName.value = '';
  playerColor.value = '#000000';

  modalPlayerUpdate.value.do = false;
  modalPlayerUpdate.value.modalTitle = '';
  modalPlayerUpdate.value.action = '';
  modalPlayerUpdate.value.player.name = '';
};

const prepareAdd = () => {
  modalPlayerUpdate.value.action = 'add';
  modalPlayerUpdate.value.modalTitle = modalPlayerUpdate.value.action.toUpperCase();
  modalPlayerUpdate.value.player.name = '';
  modalPlayerUpdate.value.do = true;
};

// ###################
// ###  WebAppAPI  ###
// ###################

const updatePlayersStats = async () => {
  modalPlayerUpdate.value.do = false;

  const resp = await store.addPlayer(playerName.value, playerColor.value);

  resetValues();

  return resp;
};
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}
</style>
