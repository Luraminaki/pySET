<template>

  <b-modal v-model="triggerModal" :title="modalTitle" @ok="triggerModal=false" ok-only @close="triggerModal=false" no-close-on-backdrop no-close-on-esc>
    {{ modalMessage }}
  </b-modal>

</template>

<script setup>
import { ref, onBeforeMount, watch } from "vue";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  modalGenericMessage: { type: Object, required: false, default() { return { triggerModal: false, modalTitle: '', modalMessage: '' }; } },
});

const componentName = 'ModalGenericMessage';

const emit = defineEmits(['trigger-updated']);

const triggerModal = ref(false);
const modalTitle = ref('');
const modalMessage = ref('');

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => props.modalGenericMessage.triggerModal, (newValue, oldValue) => {
    if (newValue) {
      triggerModal.value = newValue;
      modalMessage.value = props.modalGenericMessage.modalMessage;
      modalTitle.value = props.modalGenericMessage.modalTitle;
    }
  }
);

watch(
  () => triggerModal.value, (newValue, oldValue) => {
    if (!newValue){
      modalMessage.value = '';
      modalTitle.value = '';
      emit('trigger-updated', { triggerModal: newValue, modalMessage: modalMessage.value, modalTitle: modalTitle.value, from: [componentName] });
    }
  }
);
</script>