#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import enum
#pylint: disable=wrong-import-order, wrong-import-position

#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


class Shape (enum.Enum):
    DIAMOND = enum.auto()
    SQUIGGLE = enum.auto()
    OVAL = enum.auto()


class Color (enum.Enum):
    PURPLE = enum.auto()
    RED = enum.auto()
    GREEN = enum.auto()


class Shading (enum.Enum):
    OPEN = enum.auto()
    STRIPED = enum.auto()
    SOLID = enum.auto()


class Amount(enum.Enum):
    ONE = enum.auto()
    TWO = enum.auto()
    THREE = enum.auto()
