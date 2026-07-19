<template>

  <BNavbar toggleable="lg" :variant="store.theme">
    <BNavbarBrand href="#"><h1>pySET</h1></BNavbarBrand>
    <BNavbarNav>
      <BNavItem>GAME ID: {{ store.gameID }}</BNavItem>
    </BNavbarNav>
    <BNavbarToggle target="nav-collapse" />

    <BCollapse id="nav-collapse" is-nav>
      <BNavbarNav class="ms-auto mb-2 mb-lg-0">
        <HRControl/>
      </BNavbarNav>
    </BCollapse>
  </BNavbar>

  <ModalGenericMessage/>

  <div class="mt-2 is-center">

    <b-modal v-model="store.firstLaunch" title="Create / Join" no-close-on-backdrop no-close-on-esc no-footer>
      <b-accordion>
        <b-accordion-item title="NEW" visible>
          <BFormInput v-model="store.gameID" :state="store.validGameID" type="text" :placeholder="`Game ID (${store.minIDLength} characters minimum)`"/>
          <BFormInput class="mt-1" v-model="store.gameSecret" type="password" :placeholder="`Password (Leave empty if free to join)`"/>
          <BButton class="mt-2" pill :disabled="!store.validGameID" @click="store.createOrJoinGame(store.gameID, store.gameSecret)">
            CREATE / JOIN
          </BButton>
        </b-accordion-item>
        <b-accordion-item v-for="game in store.games" :key="game.game_id" :title="String(game.has_secret ? '🔒' : '') + game.game_id">
          <BFormInput v-model="store.gameSecret" v-if="game.has_secret" type="password" :placeholder="`Password`"/>
          <BButton class="mt-2" pill :disabled="game.has_secret && String(store.gameSecret) == ''" @click="store.createOrJoinGame(game.game_id, String(game.has_secret ? store.gameSecret : ''))">
            JOIN
          </BButton>
        </b-accordion-item>
      </b-accordion>
    </b-modal>

    <SetGame v-if="!store.firstLaunch"/>

    <div class="bottom">
      <div>
        <span class="badge bg-dark">version</span>
        <span class="badge bg-info">{{ store.version }}</span>
      </div>

      <div>
        <span class="badge bg-dark">games</span>
        <span :class="store.games.length < store.maxGames ? 'badge bg-success' : 'badge bg-danger'">{{ store.games.length }} / {{ store.maxGames }}</span>
      </div>
    </div>

  </div>

</template>

<script setup>
import { onMounted } from "vue";
import { useGameStore } from "~/stores/game.js";

// ##################
// #####  VARS  #####
// ##################

const store = useGameStore();

// ##################
// #####  NUXT  #####
// ##################

onMounted(async () => {
  store.initTheme();
  await store.loadConfig();
  await store.checkBackend();
});
</script>

<style scoped>
.is-center {
  display: flex;
  justify-content: center;
  align-content: center;
}
.bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100vw;
  display: flex !important;
  flex-direction: row;
  justify-content: space-between;
}
</style>
