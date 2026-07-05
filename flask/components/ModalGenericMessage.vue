<template>

  <b-modal v-model="store.modalGenericMessage.triggerModal"
           :title="store.modalGenericMessage.modalTitle"
           ok-only
           no-close-on-backdrop no-close-on-esc
           @ok="store.clearMessage()"
           @close="store.clearMessage()">
    {{ store.modalGenericMessage.modalMessage }}
  </b-modal>

</template>

<script setup>
import { useGameStore } from "~/stores/game.js";

const store = useGameStore();
</script>
