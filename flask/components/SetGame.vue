<template>
  <div class="row row-cols-2 col-8 pt-2">
    <div class="col">
      <BCard title="SET" class="h-100">
        <SetGrid/>
      </BCard>
    </div>

    <div class="col">
      <BCard :title="store.playersStats.length <= 1 ? 'PLAYER' : 'PLAYERS'" class="h-100">
        <PlayerCRUD/>

        <div class="mt-3"></div>

        <PlayerScore/>
      </BCard>
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from "~/stores/game.js";

const store = useGameStore();
</script>
