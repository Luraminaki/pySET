<template>

  <div class="is-flex">
    <div>
      <p>Penalty time</p>
      <BProgress>
        <BProgressBar v-for="(_, index) in props.playersStats" :value="playersBarPenaltyProgress[index]" :variant="variantsPenaltyProgress[index]" />
      </BProgress>
    </div>

    <div>
      <p>Submit time</p>
      <BProgress :value="submitTimeoutProgressRatio" :variant="submitTimeoutVariant" :animated="true" striped/>
    </div>
  </div>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted, watch } from "vue";
import { sendPenalty } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameState: { type: Object, required: true },
  playerState: { type: Object, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
  penalisedPlayer: { type: String, required: false, default() { return '' }},
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const config = ref({});
config.value = await useState('config').value.then(r => r);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

// Timer shenanigans
const submitSetTimeout = ref();
const submitTimeoutProgress = ref(config.value.SUBMIT_TIMEOUT_SECONDS);
const submitTimeoutProgressRatio = computed (() => {return (submitTimeoutProgress.value*100)/config.value.SUBMIT_TIMEOUT_SECONDS});
const submitTimeoutVariant = computed(() => {
  if (0 <= submitTimeoutProgressRatio.value && submitTimeoutProgressRatio.value < 33) {
    return "danger";
  }
  else if ( 33 <= submitTimeoutProgressRatio.value && submitTimeoutProgressRatio.value < 66) {
    return "warning";
  }
  else {
    return "success";
  }
});

const variantsPenaltyProgress = ref(['danger', 'warning', 'info', '']);
const playersTimerPenaltyProgress = ref([0, 0, 0, 0]);
const playersBarPenaltyProgress = computed(() => {
  const pbpp = [];

  if (props.playersStats.length != 0) {
    props.playersStats.forEach(function (_, index) {
      const playerRatioBarSection = 100 / props.playersStats.length;
      const maxTimerRatio = playersTimerPenaltyProgress.value[index] / config.value.PENALTY_TIMEOUT_SECONDS;
      pbpp.push(playerRatioBarSection * maxTimerRatio);
    });
  }
  return pbpp;
});

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
});

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => props.playerState.name, async (newValue, oldValue) => {
    if (newValue == PlayerStates.SUBMITTING.name) {
      proceedWithSelectedPlayer()
    }
    else if (newValue != PlayerStates.SUBMITTING.name && oldValue == PlayerStates.SUBMITTING.name) {
      try {
        clearTimeout(submitSetTimeout.value);
      }
      catch (error) {
        console.log(`No timeout to clear: ${error}`);
      }
    }
    else {
      console.log(`${componentName.value} ignored ${TypeStates.PLAYER.name} ${newValue}`);
    }
  }
);

watch(
  () => props.penalisedPlayer, async (newValue, oldValue) => {
    if (newValue != '') {
      sendPlayerPenalty();
      emit('update-player-state', { status: true,
                                    typeState: TypeStates.PLAYER,
                                    playerState: props.playerState,
                                    data: {action: 'player-penalty'},
                                    from: [componentName.value] });
    }
  }
);

// ###################
// #####   GUI   #####
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

const updateSubmitProgressBar = () => {
  const timer = 500;
  let progressBarEvolution = setInterval(() => {
    if (props.playerState.name != PlayerStates.SUBMITTING.name) {
     clearInterval(progressBarEvolution);
     submitTimeoutProgress.value = config.value.SUBMIT_TIMEOUT_SECONDS;
     return { status: true };
    }

    submitTimeoutProgress.value  = submitTimeoutProgress.value - (timer/1000);

    return { status: true };
  }, timer);
};

const updatePlayerPenaltyProgressBar = (playerIndex) => {
  const timer = 500;
  let progressBarEvolution = setInterval(() => {
    if (playersTimerPenaltyProgress.value[playerIndex] == 0) {
     clearInterval(progressBarEvolution);
     return { status: true };
    }

    if(props.gameState.name == GameStates.RUNNING.name){
      playersTimerPenaltyProgress.value[playerIndex]  = playersTimerPenaltyProgress.value[playerIndex] - (timer/1000);
    }

    return { status: true };
  }, timer);
};

// ###################
// #####  FUNCS  #####
// ###################

const proceedWithSelectedPlayer = () => {
  prepareForPlayerPenalty();
  updateSubmitProgressBar();

  return { status: true };
};

const prepareForPlayerPenalty = () => {
  try {
    clearTimeout(submitSetTimeout.value);
  }
  catch (error) {
    console.log(`No timeout to clear: ${error}`);
  }

  submitSetTimeout.value = setTimeout(() => {
    emit('update-player-state', { status: true,
                                  typeState: TypeStates.PLAYER,
                                  playerState: props.playerState,
                                  data: {action: 'player-penalty-request'},
                                  from: [componentName.value] });

    clearTimeout(submitSetTimeout.value);

    return { status: true };
  }, (config.value.SUBMIT_TIMEOUT_SECONDS * 1000));
}

// ###################
// ###  WebAppAPI  ###
// ###################

const sendPlayerPenalty = async () => {
  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.LOCKED,
                                data: {action: ''},
                                from: [componentName.value] });

  let playerIndex = 0;
  function findPlayerByName(player, index) {
    playerIndex = index;
    return player.name == props.penalisedPlayer;
  }

  const player = props.playersStats.filter(findPlayerByName);
  if (player.length == 0) {
    modalGenericMessage.value.modalMessage = `Player ${props.penalisedPlayer} not found`;
    modalGenericMessage.value.modalTitle = 'Not found';
    modalGenericMessage.value.triggerModal = true;

    emit('update-player-state', { status: true,
                                  typeState: TypeStates.PLAYER,
                                  playerState: PlayerStates.IDLE,
                                  data: {action: ''},
                                  from: [componentName.value] });
    return { status: false };
  }

  emit('update-game-state', { status: true,
                              typeState: TypeStates.GAME,
                              gameState: props.gameState,
                              data: {action: 'untoggle-request'},
                              from: [componentName.value] });

  const resp = await sendPenalty(modalGenericMessage, { playerName: props.penalisedPlayer });
  if (!resp.status) {
    emit('update-player-state', { status: true,
                                  typeState: TypeStates.PLAYER,
                                  playerState: PlayerStates.IDLE,
                                  data: {action: ''},
                                  from: [componentName.value] });
    return { status: resp.status };
  }

  playersTimerPenaltyProgress.value[playerIndex] = config.value.PENALTY_TIMEOUT_SECONDS;
  updatePlayerPenaltyProgressBar(playerIndex);

  // TODO: Use a toast here
  modalGenericMessage.value.modalMessage = `${config.value.PENALTY_TIMEOUT_SECONDS}s penalty applied to ${props.penalisedPlayer}`;
  modalGenericMessage.value.modalTitle = 'Applying penalty';
  modalGenericMessage.value.triggerModal = true;

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.UPDATE,
                                data: {action: ''},
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
