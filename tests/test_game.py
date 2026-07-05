"""Tests for pyset.modules.game.game.Game."""

import pytest

from pyset.modules.game.game import Game, GameState
from pyset.modules.game.set import Grid


@pytest.fixture
def game() -> Game:
    new_game = Game(Grid())
    new_game.set_penalty_time(0)
    new_game.set_max_player(2)
    return new_game


def test_add_player_success(game: Game):
    result = game.add_player('alice')

    assert result.status is True
    assert result.error == ''
    assert [player.get_stats().name for player in game.get_players()] == ['alice']


def test_add_player_name_is_none(game: Game):
    result = game.add_player(None)

    assert result.status is False
    assert result.error == 'PLAYER_NAME_IS_NONE'


def test_add_player_rejects_duplicate_name(game: Game):
    game.add_player('alice')
    result = game.add_player('alice')

    assert result.status is False
    assert result.error == 'PLAYER_NAME_ALREADY_EXISTS'


def test_add_player_rejects_once_max_reached(game: Game):
    game.add_player('alice')
    game.add_player('bob')
    result = game.add_player('carol')

    assert result.status is False
    assert result.error == 'MAX_PLAYER_REACHED'


def test_remove_player_success(game: Game):
    game.add_player('alice')
    result = game.remove_player('alice')

    assert result.status is True
    assert game.get_players() == []


def test_remove_player_not_found(game: Game):
    game.add_player('alice')
    result = game.remove_player('nobody')

    assert result.status is False
    assert result.error == 'PLAYER_DOES_NOT_EXIST'


def test_remove_player_no_players_at_all(game: Game):
    result = game.remove_player('alice')

    assert result.status is False
    assert result.error == 'NO_PLAYER'


def test_submit_set_from_player_name_valid_set(game: Game):
    game.add_player('alice')
    game.update_game(enable_pause=False)
    valid_set = game.grid.get_unique_sets_on_grid()[0]

    result = game.submit_set_from_player_name('alice', valid_set)

    assert result.status is True
    assert result.error == ''


def test_submit_set_from_player_name_unknown_player(game: Game):
    result = game.submit_set_from_player_name('nobody', [1, 2, 3])

    assert result.status is False
    assert result.error == 'PLAYER_IS_NONE'


def test_submit_set_from_player_name_game_ended(game: Game):
    game._game_state = GameState.ENDED  # simulate a finished game without exhausting the deck

    result = game.submit_set_from_player_name('alice', [1, 2, 3])

    assert result.status is False
    assert result.error == 'GAME_ENDED'


def test_apply_penalty_from_player_name(game: Game):
    game.add_player('alice')
    result = game.apply_penalty_from_player_name('alice')

    assert result.status is True
    assert game.get_players()[0].get_stats().calls == 1


def test_game_state_transitions_through_pause_and_resume(game: Game):
    assert game.get_game_state() == GameState.NEW.name

    game.update_game(enable_pause=False)
    assert game.get_game_state() == GameState.RUNNING.name

    game.update_game(enable_pause=True)
    assert game.get_game_state() == GameState.PAUSED.name

    game.update_game(enable_pause=False)
    assert game.get_game_state() == GameState.RUNNING.name
