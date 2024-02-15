<template>

  <b-accordion>
    <b-accordion-item v-for="val in props.playersStats" :key="val.name" :title="val.name">
      <li>
        <p>Player Color: <BButton :style="`background-color: ${val.color}`"></BButton></p>
      </li>
      <li>
        <p>Type: {{ val.is_ai ? "AI" : "Human" }}</p>
      </li>
      <li v-if="val.is_ai">
        <p>Difficulty: {{ val.difficulty.level.toUpperCase() }}</p>
      </li>
      <li>
        <p>Valid submit: {{ val.number_valid_sets }}</p>
      </li>
      <li>
        <p>Failed submit: {{ val.number_invalid_sets }}</p>
      </li>
      <li>
        <p>Average submit time: {{ val.average_answers_time }} seconds</p>
      </li>
      <!-- <li>
        <p>Timings: {{ val.answers_time }}</p>
      </li>
      <li>
        <p>SET found: {{ val.valid_sets }}</p>
      </li> -->
      <li v-if="showRemove">
        <p>
          <BButton @click="prepareRemove(val.name)" :disabled="disableRemove" size="sm" variant="warning">
            <p class="mdi mdi-trash-can" aria-hidden="true" style="margin-bottom: 0px;">DELETE PLAYER</p>
          </BButton>
        </p>
      </li>
    </b-accordion-item>
  </b-accordion>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

  <b-modal v-model="modalPlayerUpdate.do"
           :title="modalPlayerUpdate.modalTitle"
           @ok="updatePlayersStats()"
           @cancel="modalPlayerUpdate.do = false;"
           @close="modalPlayerUpdate.do = false">{{ modalPlayerUpdate.modalMessage }}
  </b-modal>

</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";
import { removePlayer } from "~/assets/webAppAPI.js";
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

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});
const modalPlayerUpdate = ref({ do: false, modalTitle: '', modalMessage: '', action: '', player: { name: '' } });

const showRemove = computed(() => (props.gameState == GameStates.NEW.name));
const disableRemove = computed(() => (props.playersStats.length == 0 ||
                                      props.gameState != GameStates.NEW.name ||
                                      props.playerState == PlayerStates.LOCKED.name));

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
});

// ###################
// #####   GUI   #####
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

const resetValues = () => {
  modalPlayerUpdate.value.do = false;
  modalPlayerUpdate.value.modalMessage = '';
  modalPlayerUpdate.value.modalTitle = '';
  modalPlayerUpdate.value.action = '';
  modalPlayerUpdate.value.player.name = '';
};

// ###################
// #####  FUNCS  #####
// ###################

const prepareRemove = (playerName) => {
  modalPlayerUpdate.value.action = 'remove';
  modalPlayerUpdate.value.modalMessage = `Remove player ${playerName}?`;
  modalPlayerUpdate.value.modalTitle = modalPlayerUpdate.value.action.toUpperCase();
  modalPlayerUpdate.value.player.name = playerName;
  modalPlayerUpdate.value.do = true;
};

// ###################
// ###  WebAppAPI  ###
// ###################

const updatePlayersStats = async () => {
  modalPlayerUpdate.value.do = false;

  const resp = await removePlayer(modalGenericMessage, { name: modalPlayerUpdate.value.player.name });

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