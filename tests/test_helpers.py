"""Tests for pyset.modules.misc.helpers."""

from pyset.modules.misc.helpers import int2base, most_frequent_flavor


def test_int2base_zero_uses_default_padding():
    assert int2base(0, 3) == '0000'


def test_int2base_with_explicit_padding():
    assert int2base(5, 3, padding=2) == '12'


def test_most_frequent_flavor_returns_majority():
    assert most_frequent_flavor(['a', 'a', 'b']) == 'a'


def test_most_frequent_flavor_single_value():
    assert most_frequent_flavor(['x']) == 'x'
