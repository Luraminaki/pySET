<template>

  <div class="mt-4 is-flex">
    <BButton :variant="buttonGameStateFlavor.variant" @click="changeGameStateRequest()" :disabled="!canToggleGameState">{{ buttonGameStateFlavor.text }}</BButton>
    <BButton variant="info" @click="selectSubmittingPlayer()" :disabled="!canCallSet">SET !</BButton>
    <BButton variant="outline-success" @click="sendSelection(selectedPlayer)" :disabled="!canSendSet">Submit SET</BButton>
  </div>

  <b-modal v-model="modalSelectPlayer.do" :title="modalSelectPlayer.modalTitle" @hide.prevent hide-footer>
    <div class="is-flex">
      <BButton pill v-for="player in humanPlayers" :key="player.name" @click="proceedWithSelectedPlayer(player.name)">
        {{ player.name }}
      </BButton>
    </div>
  </b-modal>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted } from "vue";
import { changeGameState, submitSet } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameState: { type: String, required: true },
  playerState: { type: String, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
  selectedCards: { type: Array, required: false, default() { return [] } },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});
const modalSelectPlayer = ref({ do: false, modalTitle: 'Select player', modalMessage: '' });

// Control variables
const canToggleGameState = computed(() => (props.playerState == PlayerStates.IDLE.name &&
                                           (props.gameState == GameStates.NEW.name ||
                                            props.gameState == GameStates.RUNNING.name ||
                                            props.gameState == GameStates.PAUSED.name) &&
                                           props.playersStats.length != 0));
const canCallSet = computed(() => (props.playerState == PlayerStates.IDLE.name &&
                                   props.gameState == GameStates.RUNNING.name &&
                                   props.playersStats.length != 0));
const canSendSet = computed(() => (props.playerState == PlayerStates.SUBMITTING.name &&
                                   props.gameState == GameStates.RUNNING.name &&
                                   props.playersStats.length != 0 &&
                                   props.selectedCards.length == 3));

// Start - Pause button cosmetic changes
const buttonGameStateFlavor = computed(() => {
  const flavor = {variant: 'secondary', text: 'Locked'};
  switch(props.gameState) {
    case GameStates.RUNNING.name:
      flavor.variant = 'warning'; flavor.text = 'Pause';
      break;
    case GameStates.PAUSED.name:
      flavor.variant = 'success'; flavor.text = 'Start';
      break;
    case GameStates.NEW.name:
      flavor.variant = 'success'; flavor.text = 'Start';
      break;
    default:
      break;
  }
  return flavor;
});

// Player list informations (Human / AI) for some automation
const isAI = (value) => value.is_ai;
const onlyAIPlayers = computed(() => (props.playersStats.every(isAI)));
const aiPlayers = computed(() => props.playersStats.filter(playersStats => playersStats.is_ai));
const humanPlayers = computed(() => props.playersStats.filter(playersStats => !playersStats.is_ai));

const selectedPlayer = ref('');

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

// ###################
// #####  FUNCS  #####
// ###################

const selectSubmittingPlayer = async () => {
  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME,
                              gameState: GameStates.IGNORE.name,
                              data: {action: 'untoggle-request'},
                              from: [componentName.value] });

  if (humanPlayers.value.length == 1) {
    const respSelectedPlayer = proceedWithSelectedPlayer(humanPlayers.value[0].name);
    return { status: respSelectedPlayer.status };
  }

  if(props.gameState == GameStates.RUNNING.name) {
    const respGameState = await changeGameStateRequest();
    if (!respGameState.status) {
      return { status: respGameState.status };
    }
  }

  modalSelectPlayer.value.do = true;

  return { status: true };
};

const proceedWithSelectedPlayer = async (playerName) => {
  modalSelectPlayer.value.do = false;

  selectedPlayer.value = playerName;

  if(props.gameState == GameStates.PAUSED.name) {
    const respGameState = await changeGameStateRequest();
    if (!respGameState.status) {
      selectedPlayer.value = '';
      return { status: respGameState.status };
    }
  }

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER.name,
                                playerState: PlayerStates.SUBMITTING.name,
                                data: {action: '', playerName: playerName},
                                from: [componentName.value] });

  return { status: true };
};

// ###################
// ###  WebAppAPI  ###
// ###################

const changeGameStateRequest = async () => {
  const enablePause = props.gameState == GameStates.RUNNING.name;
  const respGameState = await changeGameState(modalGenericMessage, {enablePause: enablePause});
  if (!respGameState.status) {
    selectedPlayer.value = '';
    return { status: respGameState.status };
  }

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME.name,
                              gameState: GameStates[respGameState.content.game_state].name,
                              data: {action: ''},
                              from: [componentName.value] });

  return { status: true };
};

const sendSelection = async (playerName) => {
  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME.name,
                              gameState: GameStates.IGNORE.name,
                              data: {action: 'untoggle-request'},
                              from: [componentName.value] });

  const respSubmit = await submitSet(modalGenericMessage, { playerName: playerName, set: props.selectedCards });
  selectedPlayer.value = '';
  if (!respSubmit.status){
    return { status: respSubmit.status };
  }

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME.name,
                              gameState: GameStates.UPDATE.name,
                              data: {action: ''},
                              from: [componentName.value] });

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER.name,
                                playerState: PlayerStates.UPDATE.name,
                                data: {action: respSubmit.content.is_valid ? '' : 'player-penalty-request'},
                                from: [componentName.value] });

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
