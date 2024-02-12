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
  gameState: { type: Object, required: true },
  playerState: { type: Object, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
  selectedCards: { type: Array, required: false, default() { return [] } },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});
const modalSelectPlayer = ref({ do: false, modalTitle: 'Select player', modalMessage: '' });

// Control variables
const canToggleGameState = computed(() => (props.playerState.name == PlayerStates.IDLE.name &&
                                           (props.gameState.name == GameStates.NEW.name ||
                                            props.gameState.name == GameStates.RUNNING.name ||
                                            props.gameState.name == GameStates.PAUSED.name) &&
                                           props.playersStats.length != 0));
const canCallSet = computed(() => (props.playerState.name == PlayerStates.IDLE.name &&
                                   props.gameState.name == GameStates.RUNNING.name &&
                                   props.playersStats.length != 0));
const canSendSet = computed(() => (props.playerState.name == PlayerStates.SUBMITTING.name &&
                                   props.gameState.name == GameStates.RUNNING.name &&
                                   props.playersStats.length != 0 &&
                                   props.selectedCards.length == 3));

// Start - Pause button cosmetic changes
const buttonGameStateFlavor = computed(() => {
  const flavor = {variant: 'secondary', text: 'Locked'};
  switch(props.gameState.name) {
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
                              gameState: props.gameState,
                              data: {action: 'untoggle-request'},
                              from: [componentName.value] });

  if (humanPlayers.value.length == 1) {
    const respSelectedPlayer = proceedWithSelectedPlayer(humanPlayers.value[0].name);
    return { status: respSelectedPlayer.status };
  }

  if(props.gameState.name == GameStates.RUNNING.name) {
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

  if(props.gameState.name == GameStates.PAUSED.name) {
    const respGameState = await changeGameStateRequest();
    if (!respGameState.status) {
      selectedPlayer.value = '';
      return { status: respGameState.status };
    }
  }

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.SUBMITTING,
                                data: {action: '', playerName: playerName},
                                from: [componentName.value] });

  return { status: true };
};

// ###################
// ###  WebAppAPI  ###
// ###################

const changeGameStateRequest = async () => {
  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.LOCKED,
                                data: {action: ''},
                                from: [componentName.value] });

  const enablePause = props.gameState.name == GameStates.RUNNING.name;
  const respGameState = await changeGameState(modalGenericMessage, {enablePause: enablePause});
  if (!respGameState.status) {
    selectedPlayer.value = '';
    emit('update-player-state', { status: true,
                                  typeState: TypeStates.PLAYER,
                                  playerState: PlayerStates.IDLE,
                                  data: {action: ''},
                                  from: [componentName.value] });
    return { status: respGameState.status };
  }

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME,
                              gameState: GameStates[respGameState.content.game_state],
                              data: {action: ''},
                              from: [componentName.value] });

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.IDLE,
                                data: {action: ''},
                                from: [componentName.value] });

  return { status: true };
};

const sendSelection = async (playerName) => {
  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.LOCKED,
                                data: {action: ''},
                                from: [componentName.value] });

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME,
                              gameState: props.gameState,
                              data: {action: 'untoggle-request'},
                              from: [componentName.value] });

  const respSubmit = await submitSet(modalGenericMessage, { playerName: playerName, set: props.selectedCards });
  selectedPlayer.value = '';
  if (!respSubmit.status){
    emit('update-player-state', { status: true,
                                  typeState: TypeStates.PLAYER,
                                  playerState: PlayerStates.IDLE,
                                  data: {action: ''},
                                  from: [componentName.value] });
    return { status: respSubmit.status };
  }

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME,
                              gameState: GameStates.UPDATE,
                              data: {action: ''},
                              from: [componentName.value] });

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.UPDATE,
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
