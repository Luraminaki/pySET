<template>

  <b-accordion>
    <b-accordion-item v-for="val in props.playersStats" :key="val.name" :title="val.name">
      <p>Player: {{ val.name }}</p>
      <p>Type: {{ val.is_IA ? "IA" : "Human" }}</p>
      <p v-if="val.is_IA">Difficulty: {{ val.difficulty.level.toUpperCase() }}</p>
      <p>Submited: {{ val.calls }}</p>
      <p>Valid submit: {{ val.number_valid_sets }}</p>
      <p>Failed submit: {{ val.number_invalid_sets }}</p>
      <p>Timings: {{ val.answers_time }}</p>
      <p>Average: {{ val.average_answers_time }}</p>
      <p>SET found: {{ val.valid_sets }}</p>
    </b-accordion-item>
  </b-accordion>

  <div :v-model="modalGenericMessage">
    <ModalGenericMessage :modalGenericMessage="modalGenericMessage" @trigger-updated="updateGenericModalMessage($event)"/>
  </div>

</template>

<script setup>
import { ref, onBeforeMount, onMounted } from "vue";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  playersStats: { type: Array, required: false, default() { return [] } },
});

const componentName = ref('');

const modalGenericMessage = ref({triggerModal: false, modalTitle: '', modalMessage: ''});

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
</script>

<style scoped>
</style>