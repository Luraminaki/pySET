import { attempt } from "~/assets/helpers.js";

export async function initSetGame(modalGenericMessage, body) {
  const resp = await attempt("app/init_set_game", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Init SET!', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getRunningGames(modalGenericMessage) {
  const resp = await attempt("app/get_running_games");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Session count', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function changeGameState(modalGenericMessage, body) {
  const resp = await attempt("app/change_game_state", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Starting / Resuming / Pausing game', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getGameState(modalGenericMessage, body) {
  const resp = await attempt("app/get_game_state", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Checking game status', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getGame(modalGenericMessage, body) {
  const resp = await attempt("app/get_game", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Fetching game datas', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function resetGame(modalGenericMessage, body) {
  const resp = await attempt("app/reset_game", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Reseting Game', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function submitSet(modalGenericMessage, body) {
  const resp = await attempt("app/submit_set", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Sending SET', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function sendPenalty(modalGenericMessage, body) {
  const resp = await attempt("app/apply_penalty", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Applying penalty', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getHints(modalGenericMessage, body) {
  const resp = await attempt("app/get_hints", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: `Fetching hints`, modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getPlayersInfos(modalGenericMessage, body) {
  const resp = await attempt("app/get_players_infos", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Fetching players datas', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function removePlayer(modalGenericMessage, body) {
  const resp = await attempt("app/remove_player", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Deleting player', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function addPlayer(modalGenericMessage, body) {
  const resp = await attempt("app/add_player", body, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Adding player', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};