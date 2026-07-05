"""Tests for pyset.view_model_app.ViewModelApp, called directly (no Flask request context)."""

import json

from pyset.view_model_app import ViewModelApp


def test_get_config_excludes_secret(vm: ViewModelApp):
    dumped = vm.get_config().model_dump()

    assert 'secret' not in dumped
    assert dumped['MAX_SESSIONS'] == 5
    assert dumped['service_id'] == 'pySET-test'


def test_get_version(vm: ViewModelApp):
    resp = vm.get_version()

    assert resp.status == 'SUCCESS'
    assert resp.version == '0.0.0-test'


def test_init_and_list_running_games(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))

    resp = vm.get_running_games()

    assert resp.status == 'SUCCESS'
    assert [game.game_id for game in resp.games] == ['g1']
    assert resp.games[0].has_secret is False


def test_add_player_flow(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))

    resp = vm.add_player(json.dumps({'gameID': 'g1', 'name': 'alice', 'color': '#ff00aa'}))

    assert resp.status == 'SUCCESS'
    assert resp.players_stats[0].name == 'alice'
    assert resp.players_stats[0].color == '#ff00aa'


def test_add_player_name_too_short(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))

    resp = vm.add_player(json.dumps({'gameID': 'g1', 'name': 'al'}))

    assert resp.status == 'ERROR'
    assert resp.error == 'INVALID_PLAYER_NAME'


def test_add_player_blocked_once_game_is_running(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))
    vm.add_player(json.dumps({'gameID': 'g1', 'name': 'alice'}))
    vm.change_game_state(json.dumps({'gameID': 'g1', 'enablePause': False}))

    resp = vm.add_player(json.dumps({'gameID': 'g1', 'name': 'bob'}))

    assert resp.status == 'ERROR'
    assert resp.error == 'NOT_ALLOWED'


def test_submit_set_cards_not_found(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))
    vm.add_player(json.dumps({'gameID': 'g1', 'name': 'alice'}))

    resp = vm.submit_set(json.dumps({'gameID': 'g1', 'playerName': 'alice', 'set': [999, 998, 997]}))

    assert resp.status == 'ERROR'
    assert resp.error == 'CARDS_NOT_FOUND'


def test_delete_running_games_requires_secret(vm: ViewModelApp):
    resp = vm.delete_running_games(json.dumps({}))
    assert resp.error == 'PARAMS_ERROR'

    resp = vm.delete_running_games(json.dumps({'secret': 'wrong'}))
    assert resp.error == 'NOT_ALLOWED'

    vm.init_set_game(json.dumps({'gameID': 'g1'}))
    resp = vm.delete_running_games(json.dumps({'secret': 'top-secret'}))
    assert resp.status == 'SUCCESS'
    assert vm.get_running_games().games == []


def test_delete_running_games_works_even_at_max_sessions(vm: ViewModelApp):
    vm.config.max_sessions = 1
    vm.init_set_game(json.dumps({'gameID': 'g1'}))

    blocked = vm.init_set_game(json.dumps({'gameID': 'g2'}))
    assert blocked.error == 'MAX_SESSIONS_REACHED'

    resp = vm.delete_running_games(json.dumps({'secret': 'top-secret'}))
    assert resp.status == 'SUCCESS'


def test_reset_game_soft_keeps_player_color(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))
    vm.add_player(json.dumps({'gameID': 'g1', 'name': 'alice', 'color': '#123456'}))

    vm.reset_game(json.dumps({'gameID': 'g1', 'hard': False}))
    resp = vm.get_players_infos(json.dumps({'gameID': 'g1'}))

    assert resp.players_stats[0].name == 'alice'
    assert resp.players_stats[0].color == '#123456'


def test_reset_game_hard_clears_roster(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1'}))
    vm.add_player(json.dumps({'gameID': 'g1', 'name': 'alice'}))

    vm.reset_game(json.dumps({'gameID': 'g1', 'hard': True}))
    resp = vm.get_players_infos(json.dumps({'gameID': 'g1'}))

    assert resp.players_stats == []


def test_wrong_game_secret_is_rejected(vm: ViewModelApp):
    vm.init_set_game(json.dumps({'gameID': 'g1', 'gameSecret': 'letmein'}))

    resp = vm.get_players_infos(json.dumps({'gameID': 'g1', 'gameSecret': 'wrong'}))

    assert resp.status == 'ERROR'
    assert resp.error == 'INVALID_SECRET'
