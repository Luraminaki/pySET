<template>
  <div class="row row-cols-2 col-8 pt-2">
    <div class="col">
      <BCard title="SET" class="h-100">
        <SetGrid :gameAuth="props.gameAuth"
                 :gameState="props.gameState"
                 :playerState="props.playerState"

                 :playersStats="props.playersStats"

                 :selectedPlayer="selectedPlayer"
                 :hintedCards="hintedCards"

                 @update-player-state="updatePlayerStateHandler($event)"
                 @update-game-state="updateGameStateHandler($event)"/>
      </BCard>
    </div>

    <div class="col">
      <BCard :title="playersStats.length <= 1 ? 'PLAYER' : 'PLAYERS'" class="h-100">
        <PlayerCRUD :gameAuth="props.gameAuth"
                    :gameState="props.gameState"
                    :playerState="props.playerState"

                    :playersStats="props.playersStats"

                    @update-player-state="updatePlayerStateHandler($event)"/>

        <div class="mt-3"></div>

        <PlayerScore :gameAuth="props.gameAuth"
                     :gameState="props.gameState"
                     :playerState="props.playerState"

                     :playersStats="props.playersStats"

                     @update-player-state="updatePlayerStateHandler($event)"/>
      </BCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";
import { PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  gameAuth: { type: Object, required: true },
  gameState: { type: String, required: true },
  playerState: { type: String, required: true },
  playersStats: { type: Array, required: false, default() { return [] } },
});

const emit = defineEmits(['update-player-state', 'update-game-state']);

const config = ref(await useConfig());

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

  emit('update-player-state', ev);

  return { status: true };
};

const updateGameStateHandler = (ev) => {
  if (ev.data.action == 'hint') {
    hintedCards.value = ev.data.hintedCards;
    return { status: true };
  }

  emit('update-game-state', ev);

  return { status: true };
};
</script>