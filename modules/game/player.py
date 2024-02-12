#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import time
from typing import List

#pylint: disable=wrong-import-order, wrong-import-position

#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


class Player():
    fold_cards_if_possible: callable

    def __init__(self, player_name='', is_ai: bool=False, difficulty: dict=None):
        self._name = player_name
        self._is_ai = is_ai
        self._difficulty = difficulty

        self._found_sets: List[tuple] = [ ]
        self._set_called = 0
        self._set_found_elapsed_time = [ ]
        self._last_penality = 0 # Timestamp


    def submit_set(self, card_set: list, timer: float) -> bool:
        if not callable(self.fold_cards_if_possible):
            raise ValueError

        found_valid = self.fold_cards_if_possible(card_set)
        if found_valid:
            self._found_sets.append(card_set)
            self._set_called = self._set_called + 1
            self._set_found_elapsed_time.append(time.time() - timer)

        else:
            self.apply_penalty()

        return found_valid


    def get_last_penalty(self) -> float:
        return self._last_penality


    def apply_penalty(self) -> float:
        self._last_penality = time.time()
        self._set_called = self._set_called + 1
        return self._last_penality


    def resume_penalty(self, elapsed_time_during_pause: float) -> float:
        self._last_penality = self._last_penality + elapsed_time_during_pause if self._last_penality != 0 else 0
        return self._last_penality


    def get_stats(self) -> dict:
        average_answers_time = 0

        if self._set_found_elapsed_time:
            average_answers_time = int(sum(self._set_found_elapsed_time)/len(self._set_found_elapsed_time))

        return { 'name': self._name,
                 'is_ai': self._is_ai,
                 'difficulty': self._difficulty,
                 'calls': self._set_called,
                 'number_invalid_sets': self._set_called - len(self._found_sets),
                 'number_valid_sets': len(self._found_sets),
                 'valid_sets': self._found_sets,
                 'average_answers_time': average_answers_time,
                 'answers_time': self._set_found_elapsed_time }
