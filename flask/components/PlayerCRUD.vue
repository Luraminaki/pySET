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

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted, watch } from "vue";
import { sleep } from "~/assets/helpers.js";
import { addPlayer } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameID: { type: String, required: true },
  gameState: { type: String, required: true },
  playerState: { type: String, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state']);

const config = ref({});
config.value = await useState('config').value.then(r => r);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});
const modalPlayerUpdate = ref({ do: false, modalTitle: '', modalMessage: '', action: '', player: { name: '' } });

const disableAdd = computed(() => (props.playersStats.length == config.value.MAX_PLAYERS ||
                                   props.gameState != GameStates.NEW.name ||
                                   props.playerState == PlayerStates.LOCKED.name));

const playerColor = ref('#000000');
const uniquePlayerColor = computed(() => (props.playersStats.filter(findPlayerByColor).length == 0));
const validPlayerColor = computed(() => (playerColor.value != ''));

const minNameLength = ref(3);
const playerName = ref('');
const uniquePlayerName = computed(() => (props.playersStats.filter(findPlayerByName).length == 0));
const validPlayerName = computed(() => (playerName.value.length >= minNameLength.value && playerName.value.length <= config.value.PLAYER_NAME_MAX_CHARS));

const validPlayer = computed(() => (validPlayerName.value && uniquePlayerName.value &&
                                    validPlayerColor.value && uniquePlayerColor.value))

function findPlayerByName(player, index) {
  return player.name == playerName.value;
}

function findPlayerByColor(player, index) {
  return player.color == playerColor.value;
}

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
});

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
// #####   GUI   #####
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

const resetValues = () => {
  playerName.value = '';
  playerColor.value = '#000000';

  modalPlayerUpdate.value.do = false;
  modalPlayerUpdate.value.modalTitle = '';
  modalPlayerUpdate.value.action = '';
  modalPlayerUpdate.value.player.name = '';
};

// ###################
// #####  FUNCS  #####
// ###################

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

  let resp = { status: false };

  resp = await addPlayer(modalGenericMessage, { gameID: props.gameID, name: playerName.value, color: playerColor.value });

  resetValues();

  if (!resp.status) {
    return { status: resp.status };
  }

  emit('update-player-state', { status: resp.status,
                                typeState: TypeStates.PLAYER.name,
                                playerState: PlayerStates.UPDATE.name,
                                data: {action: ''},
                                from: [componentName.value] } );

  return { status: true };
};
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}
</style>