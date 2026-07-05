<template>

  <BCard no-body
         img-placement="overlay" border-variant="secondary"
         :img-src="`/cards/${props.card}.png`"
         :img-alt="props.card"
         :id="`card-${props.card}`"
         :class="cardClass"
         @click="toggleCard('card border-info')"/>

</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useGameStore } from "~/stores/game.js";

// ##################
// #####  VARS  #####
// ##################

const props = defineProps({
  card: { type: Number, required: true },
});

const store = useGameStore();

const cardIsSelected = ref(false);
const cardClass = ref('card border-secondary');

const preventToggle = computed(() => (store.selectedCards.length == store.validAmountSelectedCards));

// https://stackoverflow.com/questions/59125857/how-to-watch-props-change-with-vue-composition-api-vue-3
watch(
  () => store.cardsEvent.event, async (newValue, oldValue) => {
    if (newValue == 'hint') {
      if (store.cardsEvent.cards.includes(props.card)) {
        cardIsSelected.value = false;
        await toggleCard("card border-warning");
      }
    }
    else if (newValue == 'untoggle-request') {
      cardIsSelected.value = true;
      await toggleCard();
    }
  }
);

// ###################
// #####  FUNCS  #####
// ###################

const toggleCard = async (toggleType) => {
  if (cardIsSelected.value) {
    cardClass.value = "card border-secondary";
    cardIsSelected.value = false;

    store.toggleCard(props.card, 'remove');

    return;
  }

  if (preventToggle.value) {
    return;
  }

  cardClass.value = toggleType;
  cardIsSelected.value = true;

  store.toggleCard(props.card, 'add');
};
</script>

<style scoped>
.card {
  border-top-width: 3px !important;
  border-bottom-width: 3px !important;
  border-left-width: 3px !important;
  border-right-width: 3px !important;
  margin-block:2px !important;
}

.card:hover {
  border-color: cyan !important;
}
</style>
