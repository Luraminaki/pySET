<template>

  <BNavForm class="d-flex">
    <BButton @click="getHelp()"
             class="btn btn-outline-light" type="button">
      <i class="mdi mdi-help-circle" aria-hidden="true"></i>
      HELP
    </BButton>
    <BButton @click="askReset()"
             :disabled="disableReset"
             class="btn btn-reload-alert" type="button">
      <i class="mdi mdi-reload" aria-hidden="true"></i>
      RESET
    </BButton>
  </BNavForm>

  <b-modal v-model="modalReset.do" :title="modalReset.modalTitle" @ok="modalReset.do = false" @cancel="modalReset.do = false" @close="modalReset.do = false" ok-only ok-title="Cancel">
    {{ modalReset.modalMessage }}
    <div class="is-flex">
      <BButton @click="reset(false)">
        <i class="mdi mdi-restart" aria-hidden="true"></i>
        SOFT
      </BButton>
      <BButton @click="reset(true)" variant="warning">
        <i class="mdi mdi-restart-alert" aria-hidden="true"></i>
        HARD
      </BButton>
    </div>
  </b-modal>

  <b-modal v-model="modalAbout.do" :title="modalAbout.modalTitle" @ok="modalAbout.do = false" @cancel="modalAbout.do = false" @close="modalAbout.do = false" ok-only scrollable>
    <About/>
  </b-modal>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted } from "vue";
import { resetGame } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameState: { type: String, required: true },
  playerState: { type: String, required: true },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});
const modalReset = ref({ do: false, modalTitle: 'Reset game?', modalMessage: '' });
const modalAbout = ref({ do: false, modalTitle: 'About SET!', modalMessage: '' });

const disableReset = computed(() => (props.gameState == GameStates.NEW.name ||
                                     props.playerState == PlayerStates.LOCKED.name))

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
  modalReset.value.do = false;
  return { status: true };
};

// ###################
// ###  WebAppAPI  ###
// ###################

const getHelp = async () => {
  modalAbout.value.do = true;
  return { status: true };
};

const reset = async (hardReset) => {
  modalReset.value.do = false;

  const resp = await resetGame(modalGenericMessage, { hard: hardReset });
  if (!resp.status) {
    return { status: resp.status };
  }

  resetValues();

  emit('update-game-state', { status: resp.status,
                              typeState: TypeStates.GAME.name,
                              gameState: GameStates.RESET.name,
                              data: {action: ''},
                              from: [componentName.value] });
  emit('update-player-state', { status: resp.status,
                                typeState: TypeStates.PLAYER.name,
                                playerState: PlayerStates.UPDATE.name,
                                data: {action: ''},
                                from: [componentName.value] })

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