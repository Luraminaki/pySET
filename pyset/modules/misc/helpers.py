#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import enum


class StatusFunction(enum.Enum):
    """Generic outcome status shared across the API."""

    SUCCESS = enum.auto()
    FAIL = enum.auto()
    ONGOING = enum.auto()
    DONE = enum.auto()
    ERROR = enum.auto()
    WARNING = enum.auto()


def int2base(number: int, base: int, padding: int | None = None) -> str:
    """Converts an integer (base 10) into a string (base 2~9) with 0-padding.

    This function is necessary as it uses a convenient trick to avoid the loss of the 0-padded values.

    Args:
        number (int): Number (base 10) to convert.
        base (int): Base targeted.
        padding (int | None, optional): How long the string must be (Will be filled with 0). Defaults to None.

    Returns:
        str: Converted integer.
    """
    if padding is None:
        padding = base + 1

    digits: list[str] = []

    while number:
        digits.append(str(int(number % base)))
        number //= base

    return ''.join(reversed(digits)).zfill(padding)


def most_frequent_flavor(flavors: list[str]) -> str:
    """Returns the value that appears the most in a given list.

    Args:
        flavors (list[str]): List of flavor markers.

    Returns:
        str: Most frequent flavor marker.
    """
    return max(set(flavors), key=flavors.count)
