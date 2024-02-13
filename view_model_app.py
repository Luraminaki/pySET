#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import inspect
import logging

import json

#pylint: disable=wrong-import-order, wrong-import-position
from modules.game.set import Grid
from modules.game.game import Game, GameState

from modules.web.app_factory import export
from modules.misc.helpers import StatusFunction
#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


class ViewModelApp():
    """ ViewModelApp """

    def __init__(self, conf: dict, scheme: str, subdomain: str):
        self.scheme = scheme
        self.subdomain = subdomain

        self.config = conf
        self.config['app_version'] = __version__

        self.logger = logging.getLogger("View_Model_App")
        self.logger.addHandler(logging.NullHandler())

        self.logger.info('%s version %s', self.__class__.__name__, __version__)

        self.set_game = Game(Grid())
        self.set_game.set_penalty_time(self.config.get('PENALTY_TIMEOUT_SECONDS', 20))
        self.set_game.set_max_player(self.config.get('MAX_PLAYERS', 4))

        self.ack = {"01": "DATA_RECIEVED"}
        self.errors = {"01": "PARAMS_ERROR"}


    ################################################
    #                  BASIC  API                  #
    ################################################


    @export
    def get_version(self) -> dict:
        return { 'version': self.config['version'] }


    @export
    def get_config(self) -> dict:
        return { key: self.config[key] for key in self.config }


    @export
    def get_status_enum(self) -> dict:
        return { key.name: key.name for key in StatusFunction }


    ################################################
    #                 PLAYER  API                  #
    ################################################


    @export
    def remove_player(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'players_stats': [], 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        if self.set_game.get_game_state() == GameState.RUNNING:
            return { 'status': StatusFunction.ERROR.name, 'players_stats': [], 'game_state': self.set_game.get_game_state(), 'error': 'Not allowed: Game is running' }

        player_name = data.get('name', '')

        resp = self.set_game.remove_player(player_name=player_name)

        status = StatusFunction.SUCCESS.name if resp.get('status', False) else StatusFunction.ERROR.name
        return { 'status': status,
                 'players_stats': [ player.get_stats() for player in self.set_game.get_players() ],
                 'game_state': self.set_game.get_game_state(),
                 'error': resp.get('error', '') }


    @export
    def add_player(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'players_stats': [], 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        if self.set_game.get_game_state() == GameState.RUNNING:
            return { 'status': StatusFunction.ERROR.name, 'players_stats': [], 'game_state': self.set_game.get_game_state(), 'error': 'Not allowed: Game is running' }

        player_name = data.get('name', '')[:self.config['PLAYER_NAME_MAX_CHARS']]

        if len(player_name) <= 2:
            return { 'status': StatusFunction.ERROR.name, 'players_stats': [], 'game_state': self.set_game.get_game_state(), 'error': 'Invalid player name' }

        resp = self.set_game.add_player(player_name=player_name)

        status = StatusFunction.SUCCESS.name if resp.get('status', False) else StatusFunction.ERROR.name
        return { 'status': status,
                 'players_stats': [ player.get_stats() for player in self.set_game.get_players() ],
                 'game_state': self.set_game.get_game_state(),
                 'error': resp.get('error', '') }


    @export
    def get_players_infos(self) -> dict:
        return { 'status': StatusFunction.SUCCESS.name,
                 'players_stats': [ player.get_stats() for player in self.set_game.get_players() ],
                 'game_state': self.set_game.get_game_state(),
                 'error': '' }


    @export
    def submit_set(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'is_valid': False, 'set': [], 'player_name': '', 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        player_name = data.get('playerName', '')
        card_set = data.get('set', {})

        resp = self.set_game.submit_set_from_player_name(player_name, card_set)
        self.set_game.update_game(enable_pause=False)

        return { 'status': StatusFunction.SUCCESS.name, 'is_valid': resp['status'], 'set': resp['set'], 'player_name': player_name, 'game_state': self.set_game.get_game_state(), 'error': resp['error'] }


    @export
    def apply_penalty(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        player_name = data.get('playerName', '')

        resp = self.set_game.apply_penalty_from_player_name(player_name)

        return { 'status': StatusFunction.SUCCESS.name if resp['status'] else StatusFunction.ERROR.name, 'game_state': self.set_game.get_game_state(), 'error': resp['error'] }


    ################################################
    #                  GAME  API                   #
    ################################################


    @export
    def change_game_state(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'grid': [], 'draw_pile': -1, 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        if not self.set_game.get_players():
            return { 'status': StatusFunction.ERROR.name, 'grid': [], 'draw_pile': -1, 'game_state': self.set_game.get_game_state(), 'error': 'No player found' }

        draw_pile = self.set_game.grid.get_number_cards_left_in_deck()
        grid = [[]]

        try:
            grid = self.set_game.grid.grid_to_list()

        except Exception as error:
            self.logger.error("%s -- An error occured during the grid rendering: %s", curr_func, error)
            return { 'status': StatusFunction.ERROR.name, 'grid': grid, 'draw_pile': draw_pile, 'game_state': self.set_game.get_game_state(), 'error': repr(error) }

        if self.set_game.is_game_ended():
            return { 'status': StatusFunction.ERROR.name, 'grid': grid, 'draw_pile': draw_pile, 'game_state': self.set_game.get_game_state(), 'error': 'Game ended, reset the game and start again' }

        enable_pause = data.get('enablePause', False)
        self.set_game.update_game(enable_pause)
        self.logger.info("%s -- Game is now: %s", curr_func, self.set_game.get_game_state())
        self.set_game.grid.pretty_print_grid()

        return { 'status': StatusFunction.SUCCESS.name, 'grid': grid, 'draw_pile': draw_pile, 'game_state': self.set_game.get_game_state(), 'error': '' }


    @export
    def reset_game(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s --%s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'game_state': self.set_game.get_game_state(), 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        hard_reset: bool = data.get('hard', True)
        players_stats = [ player.get_stats() for player in self.set_game.get_players() ]

        self.set_game = Game(Grid())
        self.set_game.set_penalty_time(self.config.get('PENALTY_TIMEOUT_SECONDS', 20))

        if not hard_reset and players_stats:
            for player in players_stats:
                self.set_game.add_player(player_name=player.get('name', None))

        return { 'status': StatusFunction.SUCCESS.name, 'game_state': self.set_game.get_game_state(), 'error': '' }


    @export
    def get_game(self) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        self.set_game.grid.pretty_print_grid()

        draw_pile = self.set_game.grid.get_number_cards_left_in_deck()
        grid = [[]]

        try:
            grid = self.set_game.grid.grid_to_list()

        except Exception as error:
            self.logger.error("%s -- An error occured during the grid rendering: %s", curr_func, error)
            return { 'status': StatusFunction.ERROR.name, 'grid': grid, 'draw_pile': draw_pile, 'game_state': self.set_game.get_game_state(), 'error': repr(error) }

        return { 'status': StatusFunction.SUCCESS.name, 'grid': grid, 'draw_pile': draw_pile, 'game_state': self.set_game.get_game_state(), 'error': '' }


    @export
    def get_game_state(self) -> dict:
        return { 'status': StatusFunction.SUCCESS.name, 'game_state': self.set_game.get_game_state(), 'error': '' }


    @export
    def get_hints(self) -> dict:
        unique_sets = self.set_game.grid.get_unique_sets_on_grid()
        if not unique_sets:
            return { 'status': StatusFunction.ERROR.name, 'sets': [], 'game_state': self.set_game.get_game_state(), 'error': 'No valid SET left' }

        return { 'status': StatusFunction.SUCCESS.name, 'sets': unique_sets, 'game_state': self.set_game.get_game_state(), 'error': '' }
