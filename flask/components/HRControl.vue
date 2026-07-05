<template>

  <BNavForm class="d-flex">
    <BButton @click="getHelp()"
             class="btn btn-outline-light" type="button">
      <i class="mdi mdi-help-circle" aria-hidden="true"></i>
      HELP
    </BButton>
    <BButton @click="askReset()"
             :disabled="disableReset"
             class="btn btn-reload-alert" type="button">
      <i class="mdi mdi-reload" aria-hidden="true"></i>
      RESET
    </BButton>
  </BNavForm>

  <b-modal v-model="modalReset.do" :title="modalReset.modalTitle" @ok="modalReset.do = false" @cancel="modalReset.do = false" @close="modalReset.do = false" ok-only ok-title="Cancel">
    {{ modalReset.modalMessage }}
    <div class="is-flex">
      <BButton @click="reset(false)">
        <i class="mdi mdi-restart" aria-hidden="true"></i>
        SOFT
      </BButton>
      <BButton @click="reset(true)" variant="warning">
        <i class="mdi mdi-restart-alert" aria-hidden="true"></i>
        HARD
      </BButton>
    </div>
  </b-modal>

  <b-modal v-model="modalAbout.do" :title="modalAbout.modalTitle" @ok="modalAbout.do = false" @cancel="modalAbout.do = false" @close="modalAbout.do = false" ok-only scrollable>
    <About/>
  </b-modal>

</template>

<script setup>
import { ref, computed } from "vue";
import { useGameStore } from "~/stores/game.js";
import { GameStates, PlayerStates } from "~/assets/states.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

const modalReset = ref({ do: false, modalTitle: 'Reset game?', modalMessage: '' });
const modalAbout = ref({ do: false, modalTitle: 'About SET!', modalMessage: '' });

const disableReset = computed(() => (store.gameState == GameStates.NEW.name ||
                                     store.playerState == PlayerStates.LOCKED.name))

// ###################
// #####   GUI   #####
// ###################

const askReset = () => {
  modalReset.value.do = true;
};

const resetValues = () => {
  modalReset.value.do = false;
};

// ###################
// ###  WebAppAPI  ###
// ###################

const getHelp = async () => {
  modalAbout.value.do = true;
};

const reset = async (hardReset) => {
  modalReset.value.do = false;

  const resp = await store.resetGame(hardReset);
  if (!resp.status) {
    return;
  }

  resetValues();
};
</script>

<style scoped>
.is-flex {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}
</style>
