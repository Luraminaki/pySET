#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

from pydantic import BaseModel


class PlayerStats(BaseModel):
    """Snapshot of a single player's identity and performance for the current game."""

    name: str
    color: str = '#000000'
    is_ai: bool = False
    difficulty: str | None = None
    calls: int = 0
    number_invalid_sets: int = 0
    number_valid_sets: int = 0
    valid_sets: list[list[int]] = []
    average_answers_time: int = 0
    answers_time: list[int] = []


class PlayerActionResult(BaseModel):
    """Outcome of a roster-changing or penalty action (add/remove player, apply penalty)."""

    status: bool
    error: str = ''


class SubmitSetResult(BaseModel):
    """Outcome of a player attempting to submit a set."""

    status: bool
    cards_set: list[int] = []
    error: str = ''
