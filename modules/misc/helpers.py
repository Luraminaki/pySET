#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import enum
import logging

#pylint: disable=wrong-import-order, wrong-import-position

#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


logger = logging.getLogger("Misc_Helpers")
logger.addHandler(logging.NullHandler())


class StatusFunction(enum.Enum):
    SUCCESS = enum.auto()
    FAIL = enum.auto()
    ONGOING = enum.auto()
    DONE = enum.auto()
    ERROR = enum.auto()
    WARNING = enum.auto()


def int2base(number: int, base: int, padding: int=None) -> str:
    """Converts an integer (base 10) into a string (base 2~9) with 0-padding.

    Args:
        number (int): Number (base 10) to convert.
        base (int): Base targeted.
        padding (int, optional): How long the string must be (Will be filled with 0). Defaults to None.

    Returns:
        str: Converted integer.
    """
    if padding is None:
        padding = base + 1

    digits = ''

    while number:
        digits = digits + str(int(number % base))
        number //= base

    ret = ''.join(digits[ ::-1 ])

    return ret.zfill(padding)


def most_frequent_flavor(flavors: list) -> int:
    """Returns the count of the stuff that appears the most in a given list.

    Args:
        flavors (list): List of stuff.

    Returns:
        int: Most frequent stuff count.
    """
    return max(set(flavors), key = flavors.count)
