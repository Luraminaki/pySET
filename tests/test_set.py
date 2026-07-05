"""Tests for pyset.modules.game.set.Grid."""

from itertools import combinations

import pytest

from pyset.modules.game.set import Grid


def test_grid_deals_standard_layout():
    # init_grid() deals 12 cards, then keeps drawing 3 more at a time until at least one valid set
    # is on the grid -- so the dealt size is >= 12 and a multiple of 3, not always exactly 12.
    grid = Grid()
    displayed = len(grid.get_displayed_cards())
    assert displayed >= 12
    assert displayed % 3 == 0
    assert displayed + grid.get_number_cards_left_in_deck() == 81


def test_grid_starts_with_at_least_one_valid_set():
    assert Grid().get_unique_sets_on_grid()


def test_all_time_unique_sets_count_matches_classic_set_game():
    assert Grid().get_size_all_time_unique_sets() == 1080


def test_invalid_features_raise_value_error():
    with pytest.raises(ValueError):
        Grid(features=[])


def test_draw_cards_if_possible_grows_grid_and_shrinks_deck():
    grid = Grid()
    displayed_before = len(grid.get_displayed_cards())
    deck_before = grid.get_number_cards_left_in_deck()

    assert grid.draw_cards_if_possible() is True
    assert len(grid.get_displayed_cards()) == displayed_before + 3
    assert grid.get_number_cards_left_in_deck() == deck_before - 3


def test_draw_cards_if_possible_false_when_deck_empty():
    grid = Grid()
    while grid.draw_cards_if_possible():
        pass
    assert grid.get_number_cards_left_in_deck() == 0
    assert grid.draw_cards_if_possible() is False


def test_fold_cards_if_possible_removes_a_valid_set():
    grid = Grid()
    valid_set = grid.get_unique_sets_on_grid()[0]

    assert grid.fold_cards_if_possible(valid_set) is True
    displayed = grid.get_displayed_cards()
    assert all(card not in displayed for card in valid_set)


def test_fold_cards_if_possible_rejects_invalid_set():
    grid = Grid()
    displayed = grid.get_displayed_cards()
    valid_sets = {tuple(sorted(s)) for s in grid.get_unique_sets_on_grid()}

    invalid_candidate = next(combo for combo in combinations(displayed, 3) if tuple(sorted(combo)) not in valid_sets)

    assert grid.fold_cards_if_possible(list(invalid_candidate)) is False
    assert set(grid.get_displayed_cards()) == set(displayed)


def test_arrange_cards_to_grid_shape():
    grid = Grid()
    rows = grid.arrange_cards_to_grid()
    assert len(rows) * 3 == len(grid.get_displayed_cards())
    assert all(len(row) == 3 for row in rows)
