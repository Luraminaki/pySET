import { attempt } from "/assets/helpers.js";

export async function changeGameState(modalGenericMessage, stateBody) {
  const resp = await attempt("app/change_game_state", stateBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Starting / Resuming / Pausing game', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getGameState(modalGenericMessage) {
  const resp = await attempt("app/get_game_state");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Checking game status', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getGame(modalGenericMessage) {
  const resp = await attempt("app/get_game");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Fetching game datas', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function resetGame(modalGenericMessage, resetBody) {
  const resp = await attempt("app/reset_game", resetBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Reseting Game', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function submitSet(modalGenericMessage, submitBody) {
  const resp = await attempt("app/submit_set", submitBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Sending SET', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function sendPenalty(modalGenericMessage, penaltyBody) {
  const resp = await attempt("app/apply_penalty", penaltyBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Applying penalty', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getHints(modalGenericMessage) {
  const resp = await attempt("app/get_hints");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: `Fetching hints`, modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function getPlayersInfos(modalGenericMessage) {
  const resp = await attempt("app/get_players_infos");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Fetching players datas', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function removePlayer(modalGenericMessage, removeBody) {
  const resp = await attempt("app/remove_player", removeBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Deleting player', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};

export async function addPlayer(modalGenericMessage, addBody) {
  const resp = await attempt("app/add_player", addBody, "POST");
  if (!resp.status) {
    modalGenericMessage.value = { triggerModal: true, modalTitle: 'Adding player', modalMessage: `Request failed: ${resp.content.error}` };
  }
  return resp;
};