#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import enum


class Shape(enum.Enum):
    """A card's shape."""

    DIAMOND = enum.auto()
    SQUIGGLE = enum.auto()
    OVAL = enum.auto()


class Color(enum.Enum):
    """A card's color."""

    PURPLE = enum.auto()
    RED = enum.auto()
    GREEN = enum.auto()


class Shading(enum.Enum):
    """A card's shading."""

    OPEN = enum.auto()
    STRIPED = enum.auto()
    SOLID = enum.auto()


class Amount(enum.Enum):
    """A card's symbol count."""

    ONE = enum.auto()
    TWO = enum.auto()
    THREE = enum.auto()
