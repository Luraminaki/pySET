<template>

  <div class="is-flex">
    <BDropdown text="Remove player" variant="" :disabled="disableRemove">
      <BDropdownItem  v-for="val in props.playersStats" :key="val.name" :title="val.name" @click="prepareRemove(val.name)">
        <span>
          <p class="mdi mdi-trash-can" aria-hidden="true">{{ val.name }}</p>
        </span>
      </BDropdownItem >
    </BDropdown>

    <BButton variant="success" @click="prepareAdd()" :disabled="disableAdd">
      <i class="mdi mdi-plus-circle-outline"></i>
      Add player
    </BButton>
  </div>

  <b-modal v-model="modalPlayerUpdate.do"
           :title="modalPlayerUpdate.modalTitle"
           :ok-disabled="modalPlayerUpdate.action == 'add' && (!validPlayerName || !uniquePlayerName)"
           @ok="updatePlayersStats()"
           @cancel="modalPlayerUpdate.do = false; playerName = ''"
           @close="modalPlayerUpdate.do = false">
    <b-form-group v-if="modalPlayerUpdate.action=='add'">
      <BFormInput v-model="playerName" :state="validPlayerName && uniquePlayerName" type="text" placeholder="Player name"/>
    </b-form-group>
    <div v-if="modalPlayerUpdate.action=='remove'">
      Remove player {{ modalPlayerUpdate.player.name }}?
    </div>
  </b-modal>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted } from "vue";
import { removePlayer, addPlayer } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
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

const disableRemove = computed(() => (props.playersStats.length == 0 ||
                                      props.gameState != GameStates.NEW.name ||
                                      props.playerState == PlayerStates.LOCKED.name));
const disableAdd = computed(() => (props.playersStats.length == config.value.MAX_PLAYERS ||
                                   props.gameState != GameStates.NEW.name ||
                                   props.playerState == PlayerStates.LOCKED.name));

const playerName = ref('');
const uniquePlayerName = computed(() => (props.playersStats.filter(findPlayerByName).length == 0));
const validPlayerName = computed(() => (playerName.value.length > 2 && playerName.value.length <= config.value.PLAYER_NAME_MAX_CHARS));

function findPlayerByName(player, index) {
  return player.name == playerName.value;
}

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
  await updatePlayersStats();
});

// ###################
// #####   GUI   #####
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

const resetValues = () => {
  playerName.value = '';

  modalPlayerUpdate.value.do = false;
  modalPlayerUpdate.value.modalTitle = '';
  modalPlayerUpdate.value.action = '';
  modalPlayerUpdate.value.player.name = '';
};

// ###################
// #####  FUNCS  #####
// ###################

const prepareRemove = (playerName) => {
  modalPlayerUpdate.value.action = 'remove';
  modalPlayerUpdate.value.modalTitle = modalPlayerUpdate.value.action.toUpperCase();
  modalPlayerUpdate.value.player.name = playerName;
  modalPlayerUpdate.value.do = true;
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

  const updateBody = { name: playerName.value };
  let resp = { status: false };

  if (modalPlayerUpdate.value.action == 'add') {
    if (updateBody.name.length <= 2) {
      modalGenericMessage.value.modalTitle = 'Error input';
      modalGenericMessage.value.modalMessage = 'Invalid player name';
      modalGenericMessage.value.triggerModal = true;
      return resp;
    }

    resp = await addPlayer(modalGenericMessage, updateBody);
  }

  else if (modalPlayerUpdate.value.action == 'remove') {
    updateBody.name = modalPlayerUpdate.value.player.name;
    resp = await removePlayer(modalGenericMessage, updateBody);
  }

  else {
    resp.status = true;
  }

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