#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import time
from collections.abc import Callable

from pyset.modules.game.models import PlayerStats


class Player:
    """A single participant (human or AI) in a :class:`pyset.modules.game.game.Game`."""

    def __init__(
        self, player_name: str = '', player_color: str = '#000000', is_ai: bool = False, difficulty: str | None = None
    ):
        """Initializes a Player.

        Args:
            player_name (str, optional): Display name. Defaults to ''.
            player_color (str, optional): Hex color used by the frontend. Defaults to '#000000'.
            is_ai (bool, optional): Whether this player is bot-controlled. Defaults to False.
            difficulty (str | None, optional): AI difficulty tier, if any. Defaults to None.
        """
        self._name = player_name
        self._color = player_color
        self._is_ai = is_ai
        self._difficulty = difficulty

        self._found_sets: list[list[int]] = []
        self._set_called = 0
        self._set_found_elapsed_time: list[int] = []
        self._last_penalty = 0.0  # Timestamp

    @property
    def name(self) -> str:
        """str: This player's display name.

        A plain attribute read; prefer this over ``get_stats().name`` when only the name is
        needed, since building a full ``PlayerStats`` snapshot copies every stat list for nothing.
        """
        return self._name

    @property
    def is_ai(self) -> bool:
        """bool: Whether this player is bot-controlled (see :meth:`name` for why this exists)."""
        return self._is_ai

    def submit_set(
        self, card_set: list[int], timer: float, fold_cards_if_possible: Callable[[list[int]], bool]
    ) -> bool:
        """Attempts to fold the given cards off the grid on this player's behalf.

        Args:
            card_set (list[int]): Cards the player claims form a valid set.
            timer (float): Timestamp the current round started at, used to measure answer time.
            fold_cards_if_possible (Callable[[list[int]], bool]): Bound to the game's
                :meth:`pyset.modules.game.set.Grid.fold_cards_if_possible`, injected by the caller
                instead of stored on the instance to avoid holding a live reference to the grid.

        Returns:
            bool: True if the set was valid and folded, False otherwise (penalty is applied).
        """
        found_valid = fold_cards_if_possible(card_set)
        if found_valid:
            self._found_sets.append(card_set)
            self._set_called = self._set_called + 1
            self._set_found_elapsed_time.append(int(time.time() - timer))

        else:
            self.apply_penalty()

        return found_valid

    def get_last_penalty(self) -> float:
        """Returns the timestamp of the last penalty applied to this player.

        Returns:
            float: Timestamp, or 0 if no penalty has ever been applied.
        """
        return self._last_penalty

    def apply_penalty(self) -> float:
        """Applies a penalty to this player, starting the penalty timeout clock.

        Returns:
            float: Timestamp the penalty was applied at.
        """
        self._last_penalty = time.time()
        self._set_called = self._set_called + 1
        return self._last_penalty

    def resume_penalty(self, elapsed_time_during_pause: float) -> float:
        """Shifts the last penalty timestamp forward by the duration the game was paused.

        Args:
            elapsed_time_during_pause (float): Seconds the game spent paused.

        Returns:
            float: Updated penalty timestamp.
        """
        self._last_penalty = self._last_penalty + elapsed_time_during_pause if self._last_penalty != 0 else 0
        return self._last_penalty

    def get_stats(self) -> PlayerStats:
        """Builds a snapshot of this player's current statistics.

        Returns:
            PlayerStats: Identity and performance snapshot.
        """
        average_answers_time = 0

        if self._set_found_elapsed_time:
            average_answers_time = int(sum(self._set_found_elapsed_time) / len(self._set_found_elapsed_time))

        return PlayerStats(
            name=self._name,
            color=self._color,
            is_ai=self._is_ai,
            difficulty=self._difficulty,
            calls=self._set_called,
            number_invalid_sets=self._set_called - len(self._found_sets),
            number_valid_sets=len(self._found_sets),
            valid_sets=self._found_sets,
            average_answers_time=average_answers_time,
            answers_time=self._set_found_elapsed_time,
        )
