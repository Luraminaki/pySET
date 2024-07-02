#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import time
from itertools import combinations

import copy

import math
import random

#pylint: disable=wrong-import-order, wrong-import-position
from modules.game.features import Shape, Color, Shading, Amount
from modules.misc.helpers import int2base, most_frequent_flavor
#pylint: enable=wrong-import-order, wrong-import-position
#===================================================================================================


__version__ = '0.1.0'


class Grid():
    def __init__(self, features: list=None, find_all_unique_sets: bool=False):
        self._rand = random.Random()

        self._features = features if features is not None else [ Shape, Color, Shading, Amount ]

        if not self._is_valid_features():
            raise ValueError

        self._rows = len(self._features[0]) # 3
        self._cols = len(self._features) # 4
        self._standard_nb_cards_on_grid = self._rows * self._cols # 12
        self._cards_on_grid: list[int] = [ None ] * self._standard_nb_cards_on_grid # Default Game is played on a 4 x 3 grid

        self._shuffled_cards_id_in_deck: list[int] = [ ] # Deck filled with random integers (default range between 0 and 80 => 81 unique values)
        self._full_deck: list[int] = [ None ] * self._rows ** self._cols # Default deck has a total of 81 cards

        self._unique_sets: list[list] = [ ] # Default game has a total of 1080 unique sets
        self._unique_sets_on_grid: list[list] = [ ]

        self._init_all_cards()
        self.init_grid(find_all_unique_sets)


    #
    # INITIALISATION
    #


    def _is_valid_features(self) -> bool:
        """Sanity check of the provided features.

        Returns:
            bool: True if valid, False if not.
        """
        if self._features and 2 <= len(self._features[0]) <= 9 and len(self._features) == len(self._features[0]) + 1:
            return all(len(self._features[0]) == len(feature) for feature in self._features)
        return False


    def _init_all_cards(self) -> None:
        """Creates the cards of the deck.
        """
        for pos, _ in enumerate(self._full_deck):
            self._full_deck[pos] = self._get_int_from_flavors(int2base(pos, self._rows))
        self._full_deck.sort()


    def init_grid(self, find_all_unique_sets: bool=False) -> None:
        """Creates the playground: Card distribution, possible sets on the playground.

        Args:
            find_all_unique_sets (bool, optional): Sanity check, makes the grid initialisation slower, but gives an exhaustive list of all the valid set if all the cards were on the playground. Defaults to False.
        """
        # Shuffle deck
        self._shuffled_cards_id_in_deck = list(range(len(self._full_deck)))
        self._rand.shuffle(self._shuffled_cards_id_in_deck)

        # Create the grid
        self._cards_on_grid = [ self._full_deck[card_id] for card_id in self._shuffled_cards_id_in_deck[:self._standard_nb_cards_on_grid] ]
        del self._shuffled_cards_id_in_deck[:self._standard_nb_cards_on_grid]

        # Find all the possible valid set
        if find_all_unique_sets:
            self._unique_sets = self._find_all_valid_set_from(self._full_deck)

        # Find all possible valid set from the current grid
        self._unique_sets_on_grid = self._find_all_valid_set_from(self._cards_on_grid)

        # Draw 3 more cards as long as no set are found in the current grid
        while not self._unique_sets_on_grid:
            self.draw_cards_if_possible()
            self._unique_sets_on_grid = self._find_all_valid_set_from(self._cards_on_grid)


    #
    # TOOLS
    #


    def _get_int_from_flavors(self, flavors: str) -> int:
        """Converts a string of numbers (base 2~9) into an integer (same base with a twist).
        This function is necessary as it uses a convenient trick to avoid the loss of the 0-padded values.
        Each unit represents a flavor.

        Args:
            flavors (str): Flavors.

        Returns:
            int: Flavors to integer.
        """
        return int(flavors) + int('1'*self._cols)


    def _is_valid_set(self, card_set: list) -> bool:
        """Sanity check for a set that abides with the following rule: If you can sort a group of X cards into "X - 1 of ____ and 1 of ____", then it is not a set.

        Args:
            card_set (list): list of integers which represents a card's flavor.

        Returns:
            bool: True if valid, False if not.
        """
        grouped_flavors = [ ]
        any_sub_valid = False

        for card in card_set:
            grouped_flavors.append([*str(card)])

        grouped_flavors = [[row[i] for row in grouped_flavors] for i in range(len(grouped_flavors[0]))] # Equivalent to np.transpose(grouped_flavors)
        for flavor in grouped_flavors:
            any_sub_valid = any_sub_valid or list(flavor).count(most_frequent_flavor(list(flavor))) not in (1, self._rows)

        return not any_sub_valid


    def _find_all_valid_set_from(self, card_list: list) -> list[list[int]] | list:
        """Returns a list of all the valid set from a list of cards.

        Args:
            card_list (list): list of cards (possibly a playground).

        Returns:
            list[list[int]] | list: Either an empty list of a list of all the valid set found.
        """
        all_valid_sets = [ ]
        card_sets = list(combinations(card_list, self._rows))

        for card_set in card_sets:
            if self._is_valid_set(list(card_set)):
                valid_card_set = list(card_set)
                valid_card_set.sort()
                all_valid_sets.append(valid_card_set)

        return all_valid_sets


    def _split_list(self, list_to_split: list[int], chunk_size: int) -> list[list[int]] | list:
        """Returns a list of list of a desired lenght

        Args:
            list_to_split (list[int]): Flatlist to split
            chunk_size (int): lenght of the sublist

        Returns:
            list[list[int]] | list: list of sublist
        """
        return [list_to_split[i:i + chunk_size] for i in range(0, len(list_to_split), chunk_size)]


    #
    # CRUD (PUBLIC)
    #


    def arrange_cards_to_grid(self) -> list[list[int]] | list:
        """Returns the current state of the grid, but as a list of list.

        Returns:
            list: list of list of 3 cards (or an empty list).
        """
        return self._split_list(self.get_displayed_cards(), self._rows)


    def get_displayed_cards(self) -> list[int] | list:
        """Returns the list of cards currently on display

        Returns:
            list[int]: list of cards
        """
        return copy.deepcopy(self._cards_on_grid)


    def get_size_all_time_unique_sets(self) -> int:
        """Returns the number of possible sets one can make from the whole deck.

        Returns:
            int: Number of possible sets from the whole deck.
        """
        n = self._rows ** self._cols
        sub_valid = 0

        cptr = self._rows - 1
        while cptr >= 2:
            sub_valid = sub_valid + math.comb(n, cptr)
            cptr = cptr - 1

        return int(sub_valid / self._rows)


    def get_all_time_unique_sets(self) -> list:
        """Returns all the unique set(s) that can be made from the whole deck.

        Returns:
            list: list of all the unique set(s) that can be made from the whole deck.
        """
        return copy.deepcopy(self._unique_sets)


    def get_unique_sets_on_grid(self) -> list:
        """Returns the unique set(s) found from the playground.

        Returns:
            list: list of the unique set(s) found from the playground.
        """
        return copy.deepcopy(self._unique_sets_on_grid)


    def get_number_cards_left_in_deck(self) -> int:
        """Returns the amount of cards left in the drawing pile.

        Returns:
            int: Cards left.
        """
        return len(self._shuffled_cards_id_in_deck)


    def update_unique_sets_on_grid(self) -> None:
        """Update the list of unique set(s) found from the playground.
        """
        self._unique_sets_on_grid = self._find_all_valid_set_from(self._cards_on_grid)


    def is_missing_cards_on_grid(self) -> bool:
        """Checks if the default amount of cards to be expected on the grid is met.

        Returns:
            bool: True if cards should be added, False if not.
        """
        return len(self._cards_on_grid) < self._standard_nb_cards_on_grid


    def draw_cards_if_possible(self) -> bool:
        """Draws cards from the pile if any card are left in the pile.

        Returns:
            bool: True if successful, False if not.
        """
        if self._shuffled_cards_id_in_deck:
            self._cards_on_grid = self._cards_on_grid + [ self._full_deck[card_id] for card_id in self._shuffled_cards_id_in_deck[:self._rows] ]
            del self._shuffled_cards_id_in_deck[:self._rows]
            return True
        return False


    def fold_cards_if_possible(self, card_set: list) -> bool:
        """Folds cards in the provided set from the playground if the set is valid.

        Args:
            card_set (list): Supposedly valid set.

        Returns:
            bool: True if successful, False if not.
        """
        if card_set and self._is_valid_set(card_set) and self._cards_on_grid and all(card in self._cards_on_grid for card in card_set):
            for card in card_set:
                self._cards_on_grid.remove(card)
            return True
        return False


    def pretty_print_grid(self) -> None:
        """Pretty prints the playground for better looking logs.
        """
        print("Grid Layout:")

        pp_grid = [[]]
        game = ""

        try:
            pp_grid = self.arrange_cards_to_grid()

        except Exception:
            print("Unexpected error occured while trying to pretty print the grid in the console...")

        for line in pp_grid:
            game = game + str(line) + "\n"

        print(game)


def main(full_init_start=False) -> None:
    # It might come in handy later...
    rand = random.Random()

    # If a 'full_init_start' has been requested (slower start), you can know and display each and every set one can do with all the cards
    # This function serves as a basic illustration as for how the game works
    # Just for fun, let's see how long it takes for a game to start
    tic = time.time()
    set_grid = Grid(find_all_unique_sets=full_init_start)
    tac = time.time() - tic

    # Let's give a rough feeling of how the playground looks
    print(f"Grid initialised in {tac} seconds")
    print(f"Found {set_grid.get_size_all_time_unique_sets()} possible sets in the whole deck")
    set_grid.pretty_print_grid()

    # This is the main loop. The game keeps going as long as there are cards to draw and sets that can be made
    while set_grid.get_number_cards_left_in_deck() != 0 or set_grid.get_unique_sets_on_grid():
        print(f"Found {len(set_grid.get_unique_sets_on_grid())} possible set")
        print(f"There are {set_grid.get_number_cards_left_in_deck()} cards left to draw")

        # Time to check if there is at least a set that can be made from the cards laid one the playground
        ret_fold = False
        if set_grid.get_unique_sets_on_grid():
            # Seems like there is at least one... Let's pick a random set (if there is more than one)
            pick = rand.choice(set_grid.get_unique_sets_on_grid())
            print(f"SET! -- Picking the following cards: {pick}\n")

            # Obviously, the algorithm won't cheat or make a mistake... But a player would
            ret_fold = set_grid.fold_cards_if_possible(pick)

            # So let's ensure that the picked set is actually a valid one
            if ret_fold:
                # Turns out it is indeed a valid set... Let's draw some cards from the pile if there are less than the minimum amount required on the playground
                if set_grid.is_missing_cards_on_grid():
                    # And if any are left in the pile that is
                    set_grid.draw_cards_if_possible()
                # Time to find all the possible set in that can be made from the cards laid one the playground
                set_grid.update_unique_sets_on_grid()

            else:
                # Oh... Turns out it wasn't a valid set... It's okay, let's keep going then
                print(f"The following pick : {pick} is not a valid set\n")

        else:
            # Oh... Turns out there is no set that can be made from the cards laid on the playground... Let's add some cards to the playground
            set_grid.draw_cards_if_possible()
            # And check when the next loop starts if there is at least a set that can be made from the cards laid on the playground
            set_grid.update_unique_sets_on_grid()

        print("#######################################################")
        # Let's give a rough feeling of how the playground looks
        set_grid.pretty_print_grid()
        # Also, let's not be too hasty, else it will end in a blink
        time.sleep(1)

    # And this is the end of the game... No card left in the pile, and no set to be made from the playground
    print("The game has ended")


if __name__ == "__main__":
    main()
