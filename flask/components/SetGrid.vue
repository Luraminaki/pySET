<template>

  <div class="is-flex">
    <p>Drawing pile: {{ drawPile }} card(s)</p>
    <p>Hint(s) requested: {{ hintsRequested }}</p>
  </div>

  <Timers :gameState="props.gameState"
          :playerState = "props.playerState"
          :playersStats="props.playersStats"
          :penalisedPlayer="penalisedPlayer"

          @update-player-state="updatePlayerStateHandler($event)"
          @update-game-state="updateGameStateHandler($event)"/>

  <!-- GRID -->
  <BOverlay class="mt-3"
            :show="showGrid"
            variant="secondary" opacity="1" blur="5px">
    <BOverlay :show="!allowPlayerGridClick"
              no-spinner
              variant="transparent" opacity="0">
      <BRow v-for="(row, index) in grid" :key="index">
        <BCol v-for="card in row" :key="card">
          <SetCard :card="card"
                   :cardsEvent="cardsEvent"
                   :preventToggle="preventToggle"

                   @card-toggled="cardHandler($event)"/>
        </BCol>
      </BRow>
    </BOverlay>
  </BOverlay>
  <!-- /GRID -->

  <TurnControl :gameState="props.gameState"
               :playerState="props.playerState"

               :playersStats="props.playersStats"
               :selectedCards="selectedCards"

               @update-player-state="updatePlayerStateHandler($event)"
               @update-game-state="updateGameStateHandler($event)"/>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, computed, onBeforeMount, onMounted, watch } from "vue";
import { getGame } from "~/assets/webAppAPI.js";
import { TypeStates, GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameState: { type: Object, required: true },
  playerState: { type: Object, required: true },
  selectedPlayer: { type: String, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
  hintedCards: { type: Array, required: false, default() { return [] } },
});

const componentName = ref('');

const emit = defineEmits(['update-player-state', 'update-game-state']);

const config = ref({});
config.value = await useState('config').value.then(r => r);

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

// Control variables
const showGrid = computed(() => (props.gameState.name == GameStates.PAUSED.name ||
                                 props.gameState.name == GameStates.NEW.name));
const allowPlayerGridClick = computed(() => (props.playerState.name == PlayerStates.SUBMITTING.name))
const preventToggle = computed(() => (selectedCards.value.length == grid.value[0].length));

const cardsEvent = ref({ cards: [], event: '' });
const resetToggleCounter = ref(0);

// Game and Player variables
const penalisedPlayer = ref('');
const selectedCards = ref([]);

const grid = ref([[]]);
const drawPile = ref(0);
const hintsRequested = ref(0);

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
  await loadGame(true)
});

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => props.gameState.name, async (newValue, oldValue) => {
    if (newValue == GameStates.RESET.name) {
      await loadGame(true);
    }
    else if (newValue == GameStates.UPDATE.name) {
      await loadGame(false);
    }
    else {
      console.log(`${componentName.value} -- ${TypeStates.GAME.name} ${newValue} not handled`);
    }
  }
);

watch(
  () => props.playerState.name, async (newValue, oldValue) => {
    if (newValue == GameStates.UPDATE.name) {
      await loadGame(false);
    }
  }
);

watch(
  () => props.hintedCards, async (newValue, oldValue) => {
    if (newValue.length != 0) {
      cardsEvent.value.cards = [...newValue];
      cardsEvent.value.event = 'hint';
      hintsRequested.value = hintsRequested.value + 1
    }
  }, {deep: true}
);

// ###################
// #####   GUI   #####
// ###################

const updateGenericModalMessage = (ev) => {
  modalGenericMessage.value = ev;
};

// ###################
// #####  FUNCS  #####
// ###################

const cardHandler = async (ev) => {
  const resp = { status: false };

  if (ev.action == 'remove') {
    const index = selectedCards.value.indexOf(ev.card);
    if (index > -1) {
      selectedCards.value.splice(index, 1);
      resp.status = true;
    }
  }
  else if (ev.action == 'add') {
    if (selectedCards.value.length < 3) {
      selectedCards.value.push(ev.card);
      resp.status = true;
    }
  }
  else {
    console.log(`${componentName.value} -- Card Action ${ev.action} not handled`);
  }

  if (cardsEvent.value.event == 'untoggle-request') {
    resetToggleCounter.value = resetToggleCounter.value + 1;
    checkResetCount();
  }

  return resp;
};

const checkResetCount = () => {
  const cards = grid.value.flat();

  if (cards.length != 0 && cards.length == resetToggleCounter.value) {
    cardsEvent.value.event = '';
    cardsEvent.value.cards = [];
    resetToggleCounter.value = 0;
  }
};

const updatePlayerStateHandler = (ev) => {
  if (ev.data.action == 'player-penalty-request') {
    penalisedPlayer.value = props.selectedPlayer;
    return { status: true };
  }
  if (ev.data.action == 'player-penalty') {
    penalisedPlayer.value = '';
    return { status: true };
  }

  const from = [...ev.from];
  from.push(componentName.value);

  emit('update-player-state', { status: ev.status,
                                typeState: ev.typeState,
                                playerState: ev.playerState,
                                data: ev.data,
                                from: from });

  return { status: true };
};

const updateGameStateHandler = (ev) => {
  if (ev.data.action == 'untoggle-request') {
    cardsEvent.value.event = 'untoggle-request'; // This will be reset in cardHandler once the reset card count is reached.
    return { status: true };
  }

  const from = [...ev.from];
  from.push(componentName.value);
  emit('update-game-state', { status: ev.status,
                              typeState: ev.typeState,
                              gameState: ev.gameState,
                              data: ev.data,
                              from: from });

  return { status: true };
};

// ###################
// ###  WebAppAPI  ###
// ###################

const loadGame = async (reload=false) => {
  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.LOCKED,
                                data: {action: ''},
                                from: [componentName.value] });

  cardsEvent.value.action = '';
  cardsEvent.value.cards = [];

  penalisedPlayer.value = '';
  selectedCards.value = [];

  if (reload) {
    hintsRequested.value = 0;
    grid.value = [[]];
    drawPile.value = 0;
  }

  const resp = await getGame(modalGenericMessage);
  if (!resp.status) {
    emit('update-game-state', { status: true,
                                  typeState: TypeStates.GAME,
                                  gameState: GameStates.UNDEFINED,
                                  data: {action: ''},
                                  from: [componentName.value] });
    return { status: resp.status };
  }

  grid.value = resp.content.grid;
  drawPile.value = resp.content.draw_pile;

  emit('update-game-state', { status: resp.status,
                              typeState: TypeStates.GAME,
                              gameState: GameStates[resp.content.game_state],
                              data: {action: ''},
                              from: [componentName.value] });

  emit('update-player-state', { status: true,
                                typeState: TypeStates.PLAYER,
                                playerState: PlayerStates.IDLE,
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
