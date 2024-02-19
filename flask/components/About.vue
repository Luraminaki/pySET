<template>
  
  <BCard img-src="/Set-game-cards.png"
         img-alt="Set-game-cards"
         img-top
         tag="article">
    <BCardText>

      <h2>pySET QUICK START</h2>
      <ul>
        <li><p>Press <b>⊕ Add player</b> to add player to the game (input a player name and a color). The game will not start without at least one player.</p></li>
        <li><p>To delete a player, click on the player name, and hit the <b>DELETE PLAYER</b> button.</p></li>
        <li><p>Press <b>START</b> to initiate the game and reveal the cards.</p></li>
        <li><p>Press <b>PAUSE</b> to pause the game and hide the cards.</p></li>
        <li><p>Press <b>RESUME</b> to resume the game where you left it.</p></li>
        <li><p>Press <b>HINT</b> to reveal a valid SET.</p></li>
        <li><p>Press <b>SET!</b> if you have found a valid set of cards, click on the cards before the submitting timer runs out, and press <b>Submit SET</b> when done selecting.</p></li>
        <li><p>Press <b>RESET</b> if you want to reset the game (<b>SOFT</b> will keep the current player(s), <b>HARD</b> will not).</p></li>
        <li><p>Submitting an invalid SET, or failling in submitting a SET on time will result in a penalty: Future SET submition will refresh the penalty <b>ONLY IF</b> the aforementioned penalised player is still under the penalty.</p></li>
      </ul>

      <h2>HISTORY</h2>
      <ul>
        <p><b>SET!</b> is a real-time card game designed by <b>Marsha Falco</b> in 1974.</p>
        <p>The game evolved out of a coding system that the designer used in her job as a geneticist. The shapes are based on those in ISO 5807.</p>
        <p><b>SET!</b> won American Mensa's Mensa Select award in 1991 and placed 9th in the 1995 Deutscher Spiele Preis.</p>
      </ul>

      <h2>PREPARATIONS</h2>
      <ul>
        <p>The game can be played alone or in group.</p>
        <p>The deck consists of 81 unique cards that vary in four features across three possibilities for each kind of feature: number of shapes (one, two, or three), shape (diamond, squiggle, oval), shading (solid, striped, or open), and color (red, green, or purple).</p>
        <p>Each possible combination of features (e.g. a card with three striped green diamonds) appears as a card precisely once in the deck.</p>
      </ul>

      <h2>RULES</h2>
      <ul>
        <p>A set consists of three cards satisfying all of these conditions:</p>
        <li><p>They all have the same number or have three different numbers.</p></li>
        <li><p>They all have the same shape or have three different shapes.</p></li>
        <li><p>They all have the same shading or have three different shadings.</p></li>
        <li><p>They all have the same color or have three different colors.</p></li>
      </ul>

      <h3>TL;DR</h3>
      <ul>
        <p>The rules of <b>SET!</b> are summarized by: If you can sort a group of three cards into "two of ____ and one of ____", then it is <b>not</b> a set.</p>
      </ul>

      <h2>MORE?</h2>
      <ul>
        <p>If you are curious about the game, you can find more about <b>SET!</b> <a href="https://en.wikipedia.org/wiki/Set_(card_game)">here</a>.</p>
        <p>If you want to have a look at the source code, want to help or report a bug, you can do it <a href="https://github.com/Luraminaki/pySET">here</a>.</p>
      </ul>

    </BCardText>
  </BCard>

</template>

<script setup>
import { onBeforeMount } from "vue";

// ##################
// #####  VARS  #####
// ##################

// ##################
// #####  NUXT  #####
// ##################

onBeforeMount(() => { });

// ###################
// ######  GUI  ######
// ###################

</script>