from random import sample, choice
from typing import List, Optional, Callable

from constants import BLANK, MAX_RACK_SIZE


class Sack:
    _values = {'a': 1, 'e': 1, 'i': 1, 'n': 1, 'o': 1, 'r': 1, 's': 1, 'w': 1, 'z': 1, 'c': 2, 'd': 2, 'k': 2, 'l': 2,
               'm': 2, 'p': 2, 't': 2, 'y': 2, 'b': 3, 'g': 3, 'h': 3, 'j': 3, 'ł': 3, 'u': 3, 'ą': 5, 'ę': 5, 'f': 5,
               'ó': 5, 'ś': 5, 'ż': 5, 'ć': 6, 'ń': 7, 'ź': 9, BLANK: 0}

    _all_letters = ['a'] * 9 + ['i'] * 8 + ['e'] * 7 + ['o'] * 6 + ['n', 'z'] * 5 + ['r', 's', 'w', 'y'] * 4 + \
                   ['c', 'd', 'k', 'l', 'm', 'p', 't'] * 3 + ['b', 'd', 'h', 'j', 'ł', 'u', BLANK] * 2 + \
                   ['ą', 'ę', 'ć', 'f', 'ń', 'ó', 'ś', 'ź', 'ż']

    @classmethod
    def get_all_letters(cls) -> List[str]:
        return cls._all_letters[:]

    @classmethod
    def get_value(cls, value) -> int:
        return cls._values.get(value)

    @classmethod
    def values_without_blank(cls) -> List[str]:
        return list(cls._values)[:-1]

    def __init__(self, label: Callable = None) -> None:
        self._letters = Sack._all_letters[:]

        self.update_label = label

    def draw(self, quantity: Optional[int] = MAX_RACK_SIZE) -> List[str]:
        if not self._letters:
            return []
        elif len(self._letters) < quantity:
            quantity = len(self._letters)

        drawn = sample(self._letters, quantity)
        self.remove_letters(drawn)

        return drawn

    def draw_one(self) -> Optional[str]:
        if not self._letters:
            return None

        drawn = choice(self._letters)
        self._letters.remove(drawn)
        self.update_label(str(len(self._letters)))

        return drawn

    def remove_letters(self, letters_to_remove: List[str]) -> None:
        for letter in letters_to_remove:
            self._letters.remove(letter)
        self.update_label(str(len(self._letters)))

    def return_letters(self, letters: List[str]) -> None:
        for letter in letters:
            self._letters.append(letter)
        self.update_label(str(len(self._letters)))

    def exchange(self, letters_to_exchange: List[str]) -> List[str]:
        if len(letters_to_exchange) > len(self._letters):
            return []
        drawn = self.draw(len(letters_to_exchange))
        self.return_letters(letters_to_exchange)
        return drawn

    def how_many_remain(self):
        return len(self._letters)

    def is_empty(self):
        return not self._letters
