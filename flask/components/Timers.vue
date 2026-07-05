<template>

  <div class="is-flex">
    <div>
      <div :title="`A player penalty lasts for ${store.config.PENALTY_TIMEOUT_SECONDS} seconds`">Penalty time</div>
      <BProgress>
        <BProgressBar v-for="(_, index) in store.playersStats" :value="playersBarPenaltyProgress[index]" :style="`background-color:${variantsPenaltyProgress[index]}`" />
      </BProgress>
    </div>

    <div>
      <div :title="`Submitting duration is ${store.config.SUBMIT_TIMEOUT_SECONDS} seconds`">Submit time</div>
      <BProgress :value="submitTimeoutProgressRatio" :variant="submitTimeoutVariant" :animated="true" striped/>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, onUnmounted, watch } from "vue";
import { useGameStore } from "~/stores/game.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

// Timer shenanigans -- purely presentational, so these stay local rather than moving to the
// store: nothing outside this component's own template needs to read them.
const submitSetTimeout = ref();
const submitIntervalId = ref(null);
const submitTimeoutProgress = ref(store.config.SUBMIT_TIMEOUT_SECONDS);
const submitTimeoutProgressRatio = computed (() => {return (submitTimeoutProgress.value*100)/store.config.SUBMIT_TIMEOUT_SECONDS});
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

const variantsPenaltyProgress = computed(() => { return store.playersStats.map(player => player.color) });
const playersTimerPenaltyProgress = ref(Array.from({length: store.config.MAX_PLAYERS}, (_, __) => 0));
const penaltyIntervalIds = ref(Array.from({length: store.config.MAX_PLAYERS}, (_, __) => null));
const playersBarPenaltyProgress = computed(() => {
  const pbpp = [];

  if (store.playersStats.length != 0) {
    store.playersStats.forEach(function (_, index) {
      const playerRatioBarSection = 100 / store.playersStats.length;
      const maxTimerRatio = playersTimerPenaltyProgress.value[index] / store.config.PENALTY_TIMEOUT_SECONDS;
      pbpp.push(playerRatioBarSection * maxTimerRatio);
    });
  }
  return pbpp;
});

// ##################
// #####  NUXT  #####
// ##################

onUnmounted(() => {
  clearTimeout(submitSetTimeout.value);
  clearInterval(submitIntervalId.value);
  penaltyIntervalIds.value.forEach((id) => {
    if (id != null) {
      clearInterval(id);
    }
  });
});

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => store.playerState, async (newValue, oldValue) => {
    if (newValue == PlayerStates.SUBMITTING.name) {
      proceedWithSelectedPlayer()
    }
    else if (newValue != PlayerStates.SUBMITTING.name && oldValue == PlayerStates.SUBMITTING.name) {
      clearTimeout(submitSetTimeout.value);
    }
  }
);

watch(
  () => store.penalisedPlayer, async (newValue, oldValue) => {
    if (newValue != '') {
      const playerName = newValue;
      store.penalisedPlayer = ''; // one-shot signal: clear immediately so a future penalty re-triggers

      const resp = await store.requestPenalty(playerName);
      if (resp.status) {
        playersTimerPenaltyProgress.value[resp.playerIndex] = store.config.PENALTY_TIMEOUT_SECONDS;
        updatePlayerPenaltyProgressBar(resp.playerIndex);
      }
    }
  }
);

// ###################
// #####  FUNCS  #####
// ###################

const updateSubmitProgressBar = () => {
  const timer = 500;

  if (submitIntervalId.value != null) {
    clearInterval(submitIntervalId.value);
  }

  submitIntervalId.value = setInterval(() => {
    if (store.playerState != PlayerStates.SUBMITTING.name) {
     clearInterval(submitIntervalId.value);
     submitIntervalId.value = null;
     submitTimeoutProgress.value = store.config.SUBMIT_TIMEOUT_SECONDS;
     return;
    }

    submitTimeoutProgress.value  = submitTimeoutProgress.value - (timer/1000);
  }, timer);
};

const updatePlayerPenaltyProgressBar = (playerIndex) => {
  const timer = 500;

  if (penaltyIntervalIds.value[playerIndex] != null) {
    clearInterval(penaltyIntervalIds.value[playerIndex]);
  }

  penaltyIntervalIds.value[playerIndex] = setInterval(() => {
    if (playersTimerPenaltyProgress.value[playerIndex] == 0) {
     clearInterval(penaltyIntervalIds.value[playerIndex]);
     penaltyIntervalIds.value[playerIndex] = null;
     return;
    }

    if(store.gameState == GameStates.RUNNING.name){
      playersTimerPenaltyProgress.value[playerIndex]  = playersTimerPenaltyProgress.value[playerIndex] - (timer/1000);
    }

    if(store.gameState == GameStates.NEW.name){
      playersTimerPenaltyProgress.value[playerIndex] = 0;
    }
  }, timer);
};

const proceedWithSelectedPlayer = () => {
  prepareForPlayerPenalty();
  updateSubmitProgressBar();
};

const prepareForPlayerPenalty = () => {
  clearTimeout(submitSetTimeout.value);

  submitSetTimeout.value = setTimeout(() => {
    store.penalisedPlayer = store.selectedPlayer;
    clearTimeout(submitSetTimeout.value);
  }, (store.config.SUBMIT_TIMEOUT_SECONDS * 1000));
}
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}
</style>
