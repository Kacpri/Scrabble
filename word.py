from copy import copy
from typing import List, Optional, Dict, Tuple

from coords import Coords
from board_utils import triple_word_bonuses, double_word_bonuses, triple_letter_bonuses, double_letter_bonuses
from dictionary import Dictionary
from sack import Sack
from constants import BLANK, MAX_RACK_SIZE, MAX_GROUP_LENGTH, RIGHT, DOWN
from vector import Vector


class Word:
    _letters = Sack.values_without_blank()

    def __init__(self, rack: List[str], word: Optional[str] = '', start: Optional[Coords] = None,
                 end: Optional[Coords] = None, points: Optional[int] = 0, multiplier: Optional[int] = 1,
                 bonus: Optional[int] = 0, added_letters: Optional[Dict[Coords, Tuple[str, int]]] = None) -> None:
        self._rack = rack[:]
        self._word = word
        self._start = start
        self._end = end
        self._points = points
        self._multiplier = multiplier
        self._bonus = bonus
        if not added_letters:
            added_letters = {}
        self._added_letters = added_letters
        self._is_valid = True
        self.evaluation_points = 0

    @property
    def word(self) -> str:
        return self._word

    @property
    def start(self) -> Coords:
        return self._start

    @property
    def end(self) -> Coords:
        return self._end

    @property
    def added_letters(self) -> Dict[Coords, Tuple[str, int]]:
        return self._added_letters

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def __str__(self) -> str:
        return self._word

    def check_beginning(self) -> bool:
        self._is_valid = Dictionary.is_in_group(self._word[:MAX_GROUP_LENGTH])
        return self._is_valid

    def check_end(self) -> bool:
        self._is_valid = Dictionary.is_in_group(self._word[-MAX_GROUP_LENGTH:])
        return self._is_valid

    def is_in_dictionary(self) -> bool:
        return Dictionary.is_word_in_dictionary(self._word)

    def __copy__(self) -> 'Word':
        return Word(self._rack, self._word, self._start, self._end, self._points, self._multiplier, self._bonus,
                    self._added_letters.copy())

    def generate_child(self, letter: str, coords: Coords, extra_points: int, is_blank: Optional[bool] = False):
        child = copy(self)
        child.add_letter(letter, coords, extra_points, True, is_blank)
        if not child.is_valid:
            return None
        return child

    def generate_children(self, coords: Coords, neighbours: Optional[Tuple[List[str], int]] = None):
        children = []
        for letter in set(self._rack):
            extra_points = 0

            if neighbours:
                if letter not in neighbours[0]:
                    continue
                extra_points = neighbours[1]

            if letter == BLANK:
                for new_letter in Word._letters:
                    child = self.generate_child(new_letter, coords, extra_points, True)
                    if child:
                        children.append(child)
            else:
                child = self.generate_child(letter, coords, extra_points)
                if child:
                    children.append(child)
        return children

    def add_letter(self, letter: str, coords: Coords, extra_points: Optional[int] = 0,
                   is_from_rack: Optional[bool] = False, is_blank: Optional[bool] = False):
        if not self._start:
            self._start = coords
            self._end = coords
            self._word = letter

        elif coords < self._start:
            self._start = coords
            self._word = letter + self._word
            self.check_beginning()
        else:
            self._end = coords
            self._word = self._word + letter
            self.check_end()

        if not self.is_valid:
            return

        letter_points = Sack.get_value(letter) if not is_blank else 0

        if is_from_rack:
            self._added_letters[coords] = letter, letter_points
            self._rack.remove(letter if letter_points else BLANK)

            if coords in double_letter_bonuses:
                letter_points *= 2
            elif coords in triple_letter_bonuses:
                letter_points *= 3
            elif coords in double_word_bonuses:
                self._multiplier *= 2
            elif coords in triple_word_bonuses:
                self._multiplier *= 3

        if extra_points:
            extra_points += letter_points
            if coords in double_word_bonuses:
                extra_points *= 2
            elif coords in triple_word_bonuses:
                extra_points *= 3
            self._bonus += extra_points

        self._points += letter_points

        if len(self._added_letters) == MAX_RACK_SIZE:
            self._bonus += 50

    def sum_up(self):
        return self._points * self._multiplier + self._bonus

    def possible_prefix(self, min_length: Optional[int] = 0, max_length: Optional[int] = MAX_RACK_SIZE) -> List[str]:
        return Dictionary.find_prefixes(self._word, len(self._word), max_length, min_length)

    def possible_suffix(self, min_length: Optional[int] = 0, max_length: Optional[int] = MAX_RACK_SIZE) -> List[str]:
        return Dictionary.find_suffixes(self._word, len(self._word), max_length, min_length)

    def is_vertical(self) -> bool:
        return self._start.is_same_column(self._end)

    def is_horizontal(self) -> bool:
        return self._start.is_same_row(self._end)

    def direction(self) -> Vector:
        if self.is_vertical():
            return DOWN
        return RIGHT
