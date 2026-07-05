"""Tests for pyset.modules.game.player.Player."""

from pyset.modules.game.player import Player


def test_get_stats_defaults():
    player = Player('alice', '#ff0000')
    stats = player.get_stats()

    assert stats.name == 'alice'
    assert stats.color == '#ff0000'
    assert stats.is_ai is False
    assert stats.calls == 0
    assert stats.number_valid_sets == 0
    assert stats.number_invalid_sets == 0
    assert stats.average_answers_time == 0


def test_submit_set_valid_records_the_set():
    player = Player('alice')

    result = player.submit_set([1, 2, 3], timer=0.0, fold_cards_if_possible=lambda _cards: True)

    assert result is True
    stats = player.get_stats()
    assert stats.number_valid_sets == 1
    assert stats.number_invalid_sets == 0
    assert stats.calls == 1
    assert stats.valid_sets == [[1, 2, 3]]


def test_submit_set_invalid_applies_a_penalty():
    player = Player('alice')

    result = player.submit_set([1, 2, 3], timer=0.0, fold_cards_if_possible=lambda _cards: False)

    assert result is False
    stats = player.get_stats()
    assert stats.number_invalid_sets == 1
    assert stats.number_valid_sets == 0
    assert player.get_last_penalty() > 0


def test_resume_penalty_is_a_noop_when_never_penalized():
    player = Player('alice')
    assert player.resume_penalty(elapsed_time_during_pause=5.0) == 0


def test_resume_penalty_shifts_the_penalty_clock_forward():
    player = Player('alice')
    player.apply_penalty()
    penalty_before = player.get_last_penalty()

    resumed = player.resume_penalty(elapsed_time_during_pause=5.0)

    assert resumed == penalty_before + 5.0
    assert player.get_last_penalty() == penalty_before + 5.0
