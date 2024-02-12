<template>

  <BCard overlay border-variant="secondary"
         :img-src="`/cards/${props.card}.png`"
         :img-alt="props.card"
         :id="`card-${props.card}`"
         @click="toggleCard('card border-primary is-thick')"/>

</template>

<script setup>
import { ref, onBeforeMount, onMounted, watch } from "vue";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  card: { type: Number, required: true },
  cardsEvent: { type: Object, required: false, default() { return { cards: [], event: '' } } },
});

const emit = defineEmits(['card-toggled']);

const componentName = ref('');

const cardIsSelected = ref(false);

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

onMounted(async () => {
  componentName.value = getCurrentInstance().type.__name;
});

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => props.cardsEvent.event, async (newValue, oldValue) => {
    if (newValue == 'hint') {
      if (props.cardsEvent.cards.includes(props.card)) {
        cardIsSelected.value = false;
        await toggleCard("card border-success is-thick");
      }
    }
    else if (newValue == 'untoggle-request') {
      cardIsSelected.value = true;
      await toggleCard();
    }
    else {
      
    }
  }
);

// ###################
// #####  FUNCS  #####
// ###################

const toggleCard = async (toggleType) => {
  const cardElement = document.getElementById(`card-${props.card}`);

  if (cardIsSelected.value) {
    cardElement.className = "card border-secondary";
    cardIsSelected.value = false;

    emit('card-toggled', { status: true, action: 'remove', card: props.card, from: [componentName.value] });

    return { status: true };
  }

  cardElement.className = toggleType;
  cardIsSelected.value = true;

  emit('card-toggled', { status: true, action: 'add', card: props.card, from: [componentName.value] });

  return { status: true };
};
</script>

<style scoped>
.is-thick {
  border-top-width: 3px;
  border-bottom-width: 3px;
  border-left-width: 3px;
  border-right-width: 3px;
}
</style>