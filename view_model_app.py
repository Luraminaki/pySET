#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import time
import inspect
import logging
from typing import Union

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

        self.set_games: dict[str, dict[str, Union[Game, int]]] = {}

        self.ack = {"01": "DATA_RECIEVED",
                    "02": "DELETING_GAME",
                    "03": "DELETING_GAME_TTL_REACHED",
                    "04": "ORDER_66"}
        self.errors = {"01": "PARAMS_ERROR",
                       "02": "MAX_SESSIONS_REACHED",
                       "03": "INVALID_GAME_ID",
                       "04": "GAME_ID_ALREADY_EXISTS",
                       "05": "GAME_ID_DOES_NOT_EXIST",
                       "06": "NOT_ALLOWED",
                       "07": "INVALID_PLAYER_NAME",
                       "08": "PLAYER_NOT_FOUND",
                       "09": "SET_NOT_FOUND",
                       "10": "CARDS_NOT_FOUND",
                       "11": "INVALID_SECRET"}


    ################################################
    #              PRIVATE  FUNCTIONS              #
    ################################################


    def _clean_inactive_games(self, curr_func: str) -> None:
        if len(self.set_games) >= self.config.get('MAX_SESSIONS', 10):
            now = int(time.time())
            inactive_games = [game_id for game_id, game in self.set_games.items() if (now - game['created']) >= self.config.get('SESSION_TTL_SECONDS', 1800)]

            for game_id in inactive_games:
                last_accessed = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.set_games[game_id]['last_accessed']))
                self.logger.info("%s -- %s: %s -- last_accessed: %s", curr_func, self.ack['03'], game_id, last_accessed)
                del self.set_games[game_id]


    def _sanity_check(self, curr_func: str, params=None, ignore_empty_game_id: bool=False, ignore_empty_game_secret: bool=False, ignore_missing_game: bool=False) -> dict[str, Union[dict, str]]:
        try:
            data: dict = json.loads(params)
        except json.decoder.JSONDecodeError:
            self.logger.error("%s -- %s: %s", curr_func, self.errors['01'], params)
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['01'] }

        self.logger.info("%s -- %s: %s", curr_func, self.ack['01'], data)

        game_id = data.get('gameID', '')[:self.config['SESSION_NAME_MAX_CHARS']]
        game_secret = data.get('gameSecret', '')[:self.config['SESSION_NAME_MAX_CHARS']]

        if not ignore_empty_game_id and game_id == '':
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['03'] }

        if not ignore_missing_game and self.set_games.get(game_id, None) is None:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['05'] }

        if not ignore_empty_game_secret and self.set_games.get(game_id, None) is not None and self.set_games.get(game_id, {}).get('game_secret', '') != game_secret:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['11'] }

        if len(self.set_games) >= self.config.get('MAX_SESSIONS', 10) and self.set_games.get(game_id, None) is None:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['02'] }

        return { 'status': StatusFunction.SUCCESS.name,
                 'game_id': game_id,
                 'game_secret': game_secret,
                 'data': data,
                 'error': '' }


    def _update_game_ttl(self, curr_func: str, game_id: str) -> bool:
        try:
            self.set_games[game_id]['last_accessed'] = int(time.time())
            return True
        except Exception as err:
            self.logger.error("%s -- %s: %s", curr_func, self.ack['01'], repr(err))
            return False


    ################################################
    #                  BASIC  API                  #
    ################################################


    @export
    def get_version(self) -> dict:
        return { 'status': StatusFunction.SUCCESS.name, 'version': self.config['version'], 'error': '' }


    @export
    def get_config(self) -> dict:
        return { key: self.config[key] for key in self.config }


    @export
    def get_status_enum(self) -> dict:
        return { key.name: key.name for key in StatusFunction }


    @export
    def get_running_games(self) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        self._clean_inactive_games(curr_func)

        return { 'status': StatusFunction.SUCCESS.name,
                 'games': [ {'game_id': game_id, 'has_secret': game.get('game_secret', '') != ''} for game_id, game in self.set_games.items() ],
                 'error': '' }


    @export
    def init_set_game(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params, ignore_empty_game_id=False, ignore_missing_game=True)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        game_secret = sanity_check['game_secret']

        if self.set_games.get(game_id, None) is None:
            now = int(time.time())
            self.set_games[game_id] = {'set_game': Game(Grid()), 'game_secret': game_secret, 'created': now, 'last_accessed': now, 'ttl': self.config.get('SESSION_TTL_SECONDS', 1800)}
            self.set_games[game_id]['set_game'].set_penalty_time(self.config.get('PENALTY_TIMEOUT_SECONDS', 20))
            self.set_games[game_id]['set_game'].set_max_player(self.config.get('MAX_PLAYERS', 4))

        return { 'status': StatusFunction.SUCCESS.name, 'error': '' }


    @export
    def delete_running_games(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        self._clean_inactive_games(curr_func)

        sanity_check = self._sanity_check(curr_func, params, ignore_empty_game_id=True, ignore_empty_game_secret=True, ignore_missing_game=True)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        data = sanity_check['data']
        secret = data.get('secret', '')

        if secret == '':
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['01'] }

        if secret != self.config.get('secret', ''):
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['06'] }

        self.set_games = {}
        self.logger.info("%s -- %s: %s", curr_func, self.ack['04'], 'Lord Vader will be pleased')

        return { 'status': StatusFunction.SUCCESS.name, 'error': '' }


    ################################################
    #                 PLAYER  API                  #
    ################################################


    @export
    def remove_player(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        if self.set_games[game_id]['set_game'].get_game_state() == GameState.RUNNING:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['06'] }

        player_name = data.get('name', '')

        resp = self.set_games[game_id]['set_game'].remove_player(player_name=player_name)

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name if resp.get('status', False) else StatusFunction.ERROR.name,
                 'players_stats': [ player.get_stats() for player in self.set_games[game_id]['set_game'].get_players() ],
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': resp.get('error', '') }


    @export
    def add_player(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        if self.set_games[game_id]['set_game'].get_game_state() == GameState.RUNNING:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['06'] }

        player_name = data.get('name', '')[:self.config['PLAYER_NAME_MAX_CHARS']]
        player_color = data.get('color', '#000000')

        if len(player_name) <= 2:
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['07'] }

        resp = self.set_games[game_id]['set_game'].add_player(player_name=player_name, player_color=player_color)

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name if resp.get('status', False) else StatusFunction.ERROR.name,
                 'players_stats': [ player.get_stats() for player in self.set_games[game_id]['set_game'].get_players() ],
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': resp.get('error', '') }


    @export
    def get_players_infos(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'players_stats': [ player.get_stats() for player in self.set_games[game_id]['set_game'].get_players() ],
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }


    @export
    def submit_set(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        player_name = data.get('playerName', '')
        cards_set = data.get('set', {})

        cards_displayed = self.set_games[game_id]['set_game'].grid.get_displayed_cards()
        if not all(card in cards_displayed for card in cards_set):
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['10'] }

        resp = self.set_games[game_id]['set_game'].submit_set_from_player_name(player_name, cards_set)
        self.set_games[game_id]['set_game'].update_game(enable_pause=False)

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'is_valid': resp['status'],
                 'set': resp['set'],
                 'player_name': player_name,
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': resp['error'] }


    @export
    def apply_penalty(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        player_name = data.get('playerName', '')

        resp = self.set_games[game_id]['set_game'].apply_penalty_from_player_name(player_name)

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name if resp['status'] else StatusFunction.ERROR.name,
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': resp['error'] }


    ################################################
    #                  GAME  API                   #
    ################################################


    @export
    def change_game_state(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        if not self.set_games[game_id]['set_game'].get_players():
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['08'] }

        if self.set_games[game_id]['set_game'].is_game_ended():
            return { 'status': StatusFunction.ERROR.name, 'error': self.errors['06'] }

        enable_pause = data.get('enablePause', False)
        self.set_games[game_id]['set_game'].update_game(enable_pause)
        self.logger.info("%s -- Game is now: %s", curr_func, self.set_games[game_id]['set_game'].get_game_state())
        self.set_games[game_id]['set_game'].grid.pretty_print_grid()

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'grid': self.set_games[game_id]['set_game'].grid.arrange_cards_to_grid(),
                 'draw_pile': self.set_games[game_id]['set_game'].grid.get_number_cards_left_in_deck(),
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }


    @export
    def reset_game(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']
        data = sanity_check['data']

        hard_reset: bool = data.get('hard', True)
        players_stats = [ player.get_stats() for player in self.set_games[game_id]['set_game'].get_players() ]

        self.set_games[game_id]['set_game'] = Game(Grid())

        if not hard_reset and players_stats:
            for player in players_stats:
                self.set_games[game_id]['set_game'].add_player(player_name=player.get('name', None))

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }


    @export
    def get_game(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']

        self.set_games[game_id]['set_game'].grid.pretty_print_grid()

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'grid': self.set_games[game_id]['set_game'].grid.arrange_cards_to_grid(),
                 'draw_pile': self.set_games[game_id]['set_game'].grid.get_number_cards_left_in_deck(),
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }


    @export
    def get_game_state(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }


    @export
    def get_hints(self, params=None) -> dict:
        curr_func = inspect.currentframe().f_code.co_name

        sanity_check = self._sanity_check(curr_func, params)
        if sanity_check['status'] == StatusFunction.ERROR.name:
            return sanity_check

        game_id = sanity_check['game_id']

        self._update_game_ttl(curr_func, game_id)
        return { 'status': StatusFunction.SUCCESS.name,
                 'sets': self.set_games[game_id]['set_game'].grid.get_unique_sets_on_grid(),
                 'game_state': self.set_games[game_id]['set_game'].get_game_state(),
                 'error': '' }
