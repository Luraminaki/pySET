<template>

  <BNavForm class="d-flex">
    <BButton @click="getRandomHint()"
             :disabled="disableHint"
             class="btn btn-outline-light" type="button">
      <i class="mdi mdi-help-circle" aria-hidden="true"></i>
      HINT
    </BButton>
    <BButton @click="askReset()"
             :disabled="disableReset"
             class="btn btn-reload-alert" type="button">
      <i class="mdi mdi-reload" aria-hidden="true"></i>
      RESET
    </BButton>
  </BNavForm>

  <b-modal v-model="modalReset.do" :title="modalReset.modalTitle" @ok="reset()" @cancel="modalReset.do = false" @close="modalReset.do = false">
    {{ modalReset.modalMessage }}
    <BFormCheckbox v-model="hardReset" size="sm">Full Reset</BFormCheckbox>
  </b-modal>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted } from "vue";
import { getHints, resetGame } from "/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameState: { type: Object, required: true },
  playerState: { type: Object, required: true },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

const modalReset = ref({ do: false, modalTitle: 'Reset', modalMessage: 'Reset game?' });
const hardReset = ref(false);

const disableHint = computed(() => (props.gameState.name == GameStates.ENDED.name ||
                                    props.playerState.name == PlayerStates.SUBMITTING.name ||
                                    props.playerState.name == PlayerStates.LOCKED.name))

const disableReset = computed(() => (props.playerState.name == PlayerStates.LOCKED.name))

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

const askReset = () => {
  modalReset.value.do = true;
  return { status: true };
};

const resetValues = () => {
  hardReset.value = false;
  modalReset.value.do = false;
};

// ###################
// ###  WebAppAPI  ###
// ###################

const getRandomHint = async () => {
  const resp = await getHints(modalGenericMessage);
  if (!resp.status) {
    return { status: resp.status };
  }

  const random = Math.floor(Math.random() * resp.content.sets.length);
  emit('update-game-state', { status: resp.status,
                              typeState: TypeStates.GAME,
                              gameState: props.gameState,
                              data: {action: 'hint', hintedCards: resp.content.sets[random]},
                              from: [componentName.value] });

  return { status: true };
};

const reset = async () => {
  modalReset.value.do = false;

  const resp = await resetGame(modalGenericMessage, { hard: hardReset.value });
  if (!resp.status) {
    return { status: resp.status };
  }

  resetValues();

  emit('update-game-state', { status: resp.status,
                              typeState: TypeStates.GAME,
                              gameState: GameStates.RESET,
                              data: {action: ''},
                              from: [componentName.value] });
  emit('update-player-state', { status: resp.status,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.UPDATE,
                                data: {action: ''},
                                from: [componentName.value] })

  return { status: true };
};
</script>

<style scoped>
</style>
