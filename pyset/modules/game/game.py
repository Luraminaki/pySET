#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import enum
import random
import time
from uuid import uuid4

from pyset.modules.game.models import PlayerActionResult, SubmitSetResult
from pyset.modules.game.player import Player
from pyset.modules.game.set import Grid


class GameState(enum.Enum):
    """Lifecycle states a :class:`Game` moves through."""

    NEW = enum.auto()
    RUNNING = enum.auto()
    PAUSED = enum.auto()
    ENDED = enum.auto()
    UNDEFINED = enum.auto()


class Game:
    """Orchestrates players, timers and penalties around a :class:`pyset.modules.game.set.Grid`."""

    def __init__(self, grid: Grid):
        """Initializes a Game.

        Args:
            grid (Grid): Playground the game is played on.
        """
        self._rand = random.Random()

        self._timer = 0.0
        self._timer_paused = 0.0
        self._elapsed_time_before_pause = 0.0
        self._elapsed_time_during_pause = 0.0

        self._max_players = 4
        self._penalty_time = 20
        self._players: list[Player] = []

        self._game_state = GameState.NEW

        self.grid = grid

    def _select_player_from_name(self, player_name: str) -> tuple[Player | None, int]:
        """Finds a live player by name.

        Args:
            player_name (str): Name to look for.

        Returns:
            tuple[Player | None, int]: The player and its index, or (None, -1) if not found.
        """
        for player_id, player in enumerate(self._players):
            if player.name == player_name:
                return player, player_id
        return None, -1

    def set_penalty_time(self, penalty_time: int) -> int:
        """Sets the penalty duration.

        Args:
            penalty_time (int): Penalty duration, in seconds.

        Returns:
            int: The penalty duration that was set.
        """
        self._penalty_time = penalty_time
        return self._penalty_time

    def set_max_player(self, max_players: int) -> int:
        """Sets the maximum number of players allowed in this game.

        Args:
            max_players (int): Maximum number of players.

        Returns:
            int: The maximum that was set.
        """
        self._max_players = max_players
        return self._max_players

    def get_players(self) -> list[Player]:
        """Returns a shallow copy of the current player roster.

        A shallow copy is enough: callers only ever read the players (e.g. via ``get_stats()``),
        never mutate them, so there's no need to deep-copy each ``Player``'s internal state -- this
        just protects the internal list itself from being appended to/removed from externally.

        Returns:
            list[Player]: Players currently in the game.
        """
        return list(self._players)

    def add_player(
        self, player_name: str | None, player_color: str = '#000000', is_ai: bool = False, difficulty: str | None = None
    ) -> PlayerActionResult:
        """Adds a new player to the game.

        Args:
            player_name (str | None): Desired display name.
            player_color (str, optional): Hex color used by the frontend. Defaults to '#000000'.
            is_ai (bool, optional): Whether this player is bot-controlled. Defaults to False.
            difficulty (str | None, optional): AI difficulty tier, if any. Defaults to None.

        Returns:
            PlayerActionResult: Outcome of the operation.
        """
        if player_name is None:
            return PlayerActionResult(status=False, error='PLAYER_NAME_IS_NONE')

        if len(self._players) >= self._max_players:
            return PlayerActionResult(status=False, error='MAX_PLAYER_REACHED')

        if is_ai:
            player_name = player_name if player_name else 'bot-{}'.format(str(uuid4()).split('-', 1)[0])

        player, _ = self._select_player_from_name(player_name=player_name)
        if player is not None:
            return PlayerActionResult(status=False, error='PLAYER_NAME_ALREADY_EXISTS')

        self._players.append(Player(player_name, player_color, is_ai, difficulty))

        return PlayerActionResult(status=True)

    def remove_player(self, player_name: str) -> PlayerActionResult:
        """Removes a player from the game by name.

        Args:
            player_name (str): Name of the player to remove.

        Returns:
            PlayerActionResult: Outcome of the operation.
        """
        if not self._players:
            return PlayerActionResult(status=False, error='NO_PLAYER')

        player, player_id = self._select_player_from_name(player_name=player_name)
        if player is None:
            return PlayerActionResult(status=False, error='PLAYER_DOES_NOT_EXIST')

        del self._players[player_id]

        return PlayerActionResult(status=True)

    def submit_set_from_player_name(self, player_name: str, card_set: list[int] | None = None) -> SubmitSetResult:
        """Attempts to submit a set on behalf of a named player.

        Args:
            player_name (str): Name of the player submitting.
            card_set (list[int] | None, optional): Cards claimed to form a valid set. Ignored (and
                replaced by a random valid set) if the player is AI-controlled. Defaults to None.

        Returns:
            SubmitSetResult: Outcome of the submission.
        """
        card_set = [] if card_set is None else card_set

        if self._game_state == GameState.ENDED:
            return SubmitSetResult(status=False, cards_set=card_set, error='GAME_ENDED')

        player, player_id = self._select_player_from_name(player_name=player_name)
        if player is None:
            return SubmitSetResult(status=False, cards_set=card_set, error='PLAYER_IS_NONE')

        if player.is_ai:
            possible_sets = self.grid.get_unique_sets_on_grid()
            card_set = self._rand.choice(possible_sets)

        if int(time.time() - player.get_last_penalty()) <= self._penalty_time:
            player_name_upper = player.name.upper()
            return SubmitSetResult(
                status=False, cards_set=card_set, error=f'PLAYER_{player_name_upper}_STILL_UNDER_PENALTY'
            )

        status = player.submit_set(
            card_set, self._timer - self._elapsed_time_before_pause, self.grid.fold_cards_if_possible
        )

        if status:
            self.reset_timer()

        error = '' if status else f'INVALID_SET_PENALTY_APPLIED_TO_{player.name.upper()}'
        return SubmitSetResult(status=status, cards_set=card_set, error=error)

    def apply_penalty_from_player_name(self, player_name: str) -> PlayerActionResult:
        """Applies a penalty to a named player.

        Args:
            player_name (str): Name of the player to penalize.

        Returns:
            PlayerActionResult: Outcome of the operation.
        """
        player, _ = self._select_player_from_name(player_name=player_name)
        if player is None:
            return PlayerActionResult(status=False, error='PLAYER_IS_NONE')

        player.apply_penalty()
        return PlayerActionResult(status=True)

    def update_game(self, enable_pause: bool = False) -> None:
        """Refreshes the grid (drawing cards as needed) and toggles the timer/pause state.

        Args:
            enable_pause (bool, optional): Whether to pause the game. Defaults to False.
        """
        self.grid.update_unique_sets_on_grid()

        if self.grid.is_missing_cards_on_grid():
            self.grid.draw_cards_if_possible()
            self.grid.update_unique_sets_on_grid()

        while not self.grid.has_unique_sets_on_grid():
            if not self.grid.draw_cards_if_possible():
                break
            self.grid.update_unique_sets_on_grid()

        self.toggle_timer(enable_pause)

        if self.is_game_ended():
            self._game_state = GameState.ENDED

    def resume_players_penalty(self) -> None:
        """Shifts every player's penalty clock forward by the last pause duration."""
        for player in self._players:
            player.resume_penalty(self._elapsed_time_during_pause)

    def toggle_timer(self, enable_pause: bool = False) -> None:
        """Pauses or resumes the game timer.

        Args:
            enable_pause (bool, optional): Whether to pause the game. Defaults to False.
        """
        current_time = time.time()

        if enable_pause:
            self._game_state = GameState.PAUSED

            self._timer_paused = current_time
            self._elapsed_time_before_pause = self._elapsed_time_before_pause + self._timer_paused - self._timer

            return

        if self._timer_paused != 0:
            self._elapsed_time_during_pause = self._elapsed_time_during_pause + current_time - self._timer_paused

        self._game_state = GameState.RUNNING

        self.resume_players_penalty()

        self._timer = current_time
        self._timer_paused = 0

    def reset_timer(self) -> None:
        """Resets the round timer and pause bookkeeping."""
        self._timer = time.time()
        self._timer_paused = 0
        self._elapsed_time_before_pause = 0
        self._elapsed_time_during_pause = 0

    def is_game_ended(self) -> bool:
        """Checks whether the game has ended (no cards left, no set on the grid).

        Returns:
            bool: True if the game has ended, False otherwise.
        """
        return self.grid.get_number_cards_left_in_deck() == 0 and not self.grid.has_unique_sets_on_grid()

    def get_game_state(self) -> str:
        """Returns the current game state.

        Returns:
            str: Name of the current :class:`GameState`.
        """
        return self._game_state.name


def main() -> None:
    """Runs a scripted demo game between a single AI player and itself."""
    set_game = Game(Grid())
    set_game.add_player('', is_ai=True)

    ai_player: Player | None = None
    ai_player_name = ''

    players = set_game.get_players()
    if players and players[0].is_ai:
        ai_player = players[0]
        ai_player_name = ai_player.name

    submit_status = True

    while set_game.get_game_state() != GameState.ENDED.name:
        if submit_status:
            set_game.update_game(enable_pause=False)

        print(f'Grid Layout:\n{set_game.grid.grid_as_str()}\n')
        print(f'Deck has {set_game.grid.get_number_cards_left_in_deck()} cards left')

        # Simulating brain speed (I know, this one is very fast)
        time.sleep(0.5)

        # Simulating pause
        set_game.update_game(enable_pause=True)
        time.sleep(0.5)
        set_game.update_game(enable_pause=False)

        submit_result = set_game.submit_set_from_player_name(ai_player_name)
        submit_status = submit_result.status
        if submit_status:
            print(f'Player {ai_player_name} found a set: {submit_result.cards_set}\n')

    if ai_player is not None:
        print(f'\nPlayer {ai_player_name} stats:')
        for key, value in ai_player.get_stats().model_dump().items():
            print(f'{key}: {value}')


if __name__ == '__main__':
    main()
