<template>

  <BButton @click="showDetails = !showDetails" variant="primary">SHOW HISTORY</BButton>

  <BOffcanvas v-model="showDetails" :placement="'end'">
    <BRow v-for="(row, index) in props.playersStat.valid_sets" :key="index">
      <p>SET n° {{ index + 1 }} (Found in {{ props.playersStat.answers_time[index] }} seconds):</p>
      <BCol v-for="card in row" :key="card">
        <BCard img-placement="overlay" border-variant="secondary"
         :img-src="`/cards/${card}.png`"
         :img-alt="card"
         :id="`history-card-${card}`"/>
      </BCol>
    </BRow>
  </BOffcanvas>

</template>

<script setup>
import { ref, onBeforeMount } from "vue";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  playersStat: { type: Object, required: false, default() { return {} } },
});

const showDetails = ref(false);

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });
</script>