export class GameStates {
  static NEW = new GameStates("NEW");
  static UPDATE = new GameStates("UPDATE");
  static RESET = new GameStates("RESET");
  static RUNNING = new GameStates("RUNNING");
  static PAUSED = new GameStates("PAUSED");
  static ENDED = new GameStates("ENDED");
  static UNDEFINED = new GameStates("UNDEFINED");

  constructor(name) {
    this.name = name;
  }
};

export class PlayerStates {
  static IDLE = new PlayerStates("IDLE");
  static UPDATE = new PlayerStates("UPDATE");
  static SUBMITTING = new PlayerStates("SUBMITTING");
  static LOCKED = new PlayerStates("LOCKED");

  constructor(name) {
    this.name = name;
  }
};

export class TypeStates {
  static GAME = new TypeStates("GAME");
  static PLAYER = new TypeStates("PLAYER");

  constructor(name) {
    this.name = name;
  }
};