#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import time
import enum
from uuid import uuid4
from typing import List, Tuple

import copy
import random

#pylint: disable=wrong-import-order, wrong-import-position
from modules.game.set import Grid
from modules.game.player import Player
#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


class GameState(enum.Enum):
    NEW = enum.auto()
    RUNNING = enum.auto()
    PAUSED = enum.auto()
    ENDED = enum.auto()


class Game():
    def __init__(self, grid: Grid):
        self._rand = random.Random()

        self._timer = 0
        self._timer_paused = 0
        self._elapsed_time_before_pause = 0
        self._elapsed_time_during_pause = 0

        self._max_players = 4
        self._penalty_time = 20
        self._players: List[Player] = [ ]

        self._game_state = GameState.NEW

        self.grid = grid


    def _select_player_from_name(self, player_name: str) -> Tuple[Player | None, int]:
        for player_id, player in enumerate(self._players):
            if player.get_stats().get('name', '') == player_name:
                return player, player_id
        return None, -1


    def set_penalty_time(self, penalty_time: int) -> int:
        self._penalty_time = penalty_time
        return self._penalty_time


    def set_max_player(self, max_players: int) -> int:
        self._max_players = max_players
        return self._max_players


    def get_players(self) -> List[Player] | list:
        return copy.deepcopy(self._players)


    def add_player(self, player_name: str, is_IA: bool=False, difficulty: dict=None) -> dict:
        if player_name is None:
            return { 'status': False, 'players': self.get_players(), 'error': 'PLAYER_NAME_IS_NONE' }

        if len(self._players) >= self._max_players:
            return { 'status': False, 'players': self.get_players(), 'error': 'MAX_PLAYER_REACHED' }

        if is_IA:
            player_name = player_name if player_name else 'bot-{}'.format(str(uuid4()).split('-', 1)[0])

        player, _ = self._select_player_from_name(player_name=player_name)
        if player is not None:
            return { 'status': False, 'players':self.get_players(), 'error': 'PLAYER_NAME_ALREADY_EXISTS' }

        self._players.append(Player(player_name, is_IA, difficulty))
        self._players[-1].fold_cards_if_possible = self.grid.fold_cards_if_possible

        return { 'status': True, 'players': self.get_players(), 'error': '' }


    def remove_player(self, player_name: str) -> dict:
        if not self.get_players():
            return { 'status': False, 'players': self.get_players(), 'error': 'NO_PLAYER' }

        player, player_id = self._select_player_from_name(player_name=player_name)
        if player is None:
            return { 'status': False, 'players': self.get_players(), 'error': 'PLAYER_DOES_NOT_EXIST' }

        del self._players[player_id]

        return { 'status': True, 'players': self.get_players(), 'error': '' }


    def submit_set_from_player_name(self, player_name: str, card_set: list=None) -> dict:
        status = False
        card_set = [ ] if card_set is None else card_set

        if self._game_state.name == GameState.ENDED.name:
            return { 'status': status, 'set': card_set, 'error': 'GAME_ENDED' }

        player, _ = self._select_player_from_name(player_name=player_name)
        if player is None:
            return { 'status': status, 'set': card_set, 'error': 'PLAYER_IS_NONE' }

        if player.get_stats().get('is_IA', False):
            possible_sets = self.grid.get_unique_sets_on_grid()
            card_set = self._rand.choice(possible_sets)

        if int(time.time() - player.get_last_penalty()) <= self._penalty_time:
            return { 'status': status, 'set': card_set, 'error': 'PLAYER_{}_STILL_UNDER_PENALITY'.format(player.get_stats().get('name', '').upper()) }

        status = player.submit_set(card_set, self._timer - self._elapsed_time_before_pause)

        if status:
            self.reset_timer()

        return { 'status': status, 'set': card_set, 'error': '' if status else 'INVALID_SET + PENALITY_APPLIED_TO_{}'.format(player.get_stats().get('name', '').upper()) }


    def apply_penalty_from_player_name(self, player_name: str) -> dict:
        player, _ = self._select_player_from_name(player_name=player_name)
        if player is None:
            return { 'status': False, 'error': 'PLAYER_IS_NONE' }

        return { 'status': player.apply_penalty(), 'error': '' }


    def update_game(self, enable_pause: bool=False) -> None:
        self.grid.update_unique_sets_on_grid()

        if self.grid.is_missing_cards_on_grid():
            self.grid.draw_cards_if_possible()
            self.grid.update_unique_sets_on_grid()

        while not self.grid.get_unique_sets_on_grid():
            if not self.grid.draw_cards_if_possible():
                break
            self.grid.update_unique_sets_on_grid()

        self.toggle_timer(enable_pause)

        if self.is_game_ended():
            self._game_state = GameState.ENDED


    def resume_players_penalty(self) -> None:
        for player in self._players:
            player.resume_penalty(self._elapsed_time_during_pause)


    def toggle_timer(self, enable_pause: bool=False) -> None:
        current_time = time.time()

        if enable_pause:
            self._game_state = GameState.PAUSED

            self._timer_paused = current_time
            self._elapsed_time_before_pause = self._elapsed_time_before_pause + self._timer_paused - self._timer

            return None

        if self._timer_paused != 0:
            self._elapsed_time_during_pause = self._elapsed_time_during_pause + current_time - self._timer_paused

        self._game_state = GameState.RUNNING

        self.resume_players_penalty()

        self._timer = current_time
        self._timer_paused = 0

        return None


    def reset_timer(self) -> None:
        self._timer = time.time()
        self._timer_paused = 0
        self._elapsed_time_before_pause = 0
        self._elapsed_time_during_pause = 0


    def is_game_ended(self) -> bool:
        return self.grid.get_number_cards_left_in_deck() == 0 and not self.grid.get_unique_sets_on_grid()


    def get_game_state(self) -> GameState:
        return self._game_state.name


def main() -> None:
    ia_player: Player = None

    set_game = Game(Grid())
    players: List[Player] = set_game.add_player('', is_IA=True).get('players', [ ])

    ia_player_name = ''

    if players and players[0].get_stats().get('is_IA', False):
        ia_player: Player = players[0]
        ia_player_name = ia_player.get_stats().get('name', '')

    ret_submit = { "status": True }

    while set_game.get_game_state() != GameState.ENDED.name:
        if ret_submit.get('status', False):
            set_game.update_game(enable_pause=False)

        set_game.grid.pretty_print_grid()
        print(f"Deck has {set_game.grid.get_number_cards_left_in_deck()} cards left")

        # Simulating brain speed (I know, this one is very fast)
        time.sleep(0.5)

        # Simulating pause
        set_game.update_game(enable_pause=True)
        time.sleep(0.5)
        set_game.update_game(enable_pause=False)

        ret_submit = set_game.submit_set_from_player_name(ia_player_name)
        if ret_submit.get('status', False):
            print(f"Player {ia_player_name} found a set: {ret_submit['set']}\n")

    print(f"\nPlayer {ia_player_name} stats:")
    ret_stats = ia_player.get_stats()
    for key, value in ret_stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
