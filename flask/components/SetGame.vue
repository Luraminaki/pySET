<template>
  <BCardGroup deck class="col-8 pt-2">
    <BCard title="SET">
      <SetGrid :gameID="props.gameID"
               :gameState="props.gameState"
               :playerState="props.playerState"

               :playersStats="props.playersStats"

               :selectedPlayer="selectedPlayer"
               :hintedCards="hintedCards"

               @update-player-state="updatePlayerStateHandler($event)"
               @update-game-state="updateGameStateHandler($event)"/>
    </BCard>

    <BCard :title="playersStats.length <= 1 ? 'PLAYER' : 'PLAYERS'">
      <PlayerCRUD :gameID="props.gameID"
                  :gameState="props.gameState"
                  :playerState="props.playerState"

                  :playersStats="props.playersStats"

                  @update-player-state="updatePlayerStateHandler($event)"/>

      <div class="mt-3"></div>

      <PlayerScore :gameID="props.gameID"
                   :gameState="props.gameState"
                   :playerState="props.playerState"

                   :playersStats="props.playersStats"

                   @update-player-state="updatePlayerStateHandler($event)"/>
    </BCard >
  </BCardGroup>
</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";
import { PlayerStates } from "~/assets/states.js";

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

const emit = defineEmits(['update-player-state', 'update-game-state']);

const config = ref({});
config.value = await useState('config').value.then(r => r);

const hintedCards = ref([]);
const selectedPlayer = ref('');

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => { });

// ###################
// ######  GUI  ######
// ###################

// ###################
// #####  FUNCS  #####
// ###################

const updatePlayerStateHandler = (ev) => {
  if (ev.playerState == PlayerStates.UPDATE.name) {
    selectedPlayer.value = '';
  }
  else if (ev.playerState == PlayerStates.SUBMITTING.name) {
    selectedPlayer.value = ev.data.playerName;
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
  if (ev.data.action == 'hint') {
    hintedCards.value = ev.data.hintedCards;
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
</script>