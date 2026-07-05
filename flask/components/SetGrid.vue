<template>

  <div class="is-flex">
    <p>Drawing pile: {{ store.drawPile }} {{ store.drawPile > 1 ? "cards" : "card" }}</p>
    <p>{{ store.hintsRequested > 1 ? "Hints" : "Hint" }} requested: {{ store.hintsRequested }}</p>
  </div>

  <Timers/>

  <!-- GRID -->
  <BOverlay class="mt-3"
            :show="showGrid"
            no-spinner
            variant="secondary" opacity="1" blur="5px">
    <BOverlay :show="!allowPlayerGridClick"
              no-spinner
              variant="transparent" opacity="0">
      <BRow v-for="(row, index) in store.grid" :key="index">
        <BCol v-for="card in row" :key="card">
          <SetCard :card="card"/>
        </BCol>
      </BRow>
    </BOverlay>
  </BOverlay>
  <!-- /GRID -->

  <TurnControl/>

</template>

<script setup>
import { computed, onMounted } from "vue";
import { useGameStore } from "~/stores/game.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

// Control variables
const showGrid = computed(() => (store.gameState == GameStates.PAUSED.name ||
                                 store.gameState == GameStates.NEW.name));
const allowPlayerGridClick = computed(() => (store.playerState == PlayerStates.SUBMITTING.name))

// ##################
// #####  NUXT  #####
// ##################

onMounted(async () => {
  await store.loadGame(true);
});
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}
</style>
