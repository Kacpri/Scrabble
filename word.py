from board_utils import *
from dictionary import *
from sack import *
from constants import BLANK


class Word:
    def __init__(self, rack, neighbours, word='', points=0, multiplier=1, bonus=0, positions=None, added_letters=None):
        if not positions:
            positions = []
        if not added_letters:
            added_letters = []

        self._word = word
        self._points = points
        self._multiplier = multiplier
        self._bonus = bonus
        self._positions = positions
        self._added_letters = added_letters
        self._rack = rack[:]
        self._neighbours = neighbours
        self._is_valid = True

    @property
    def word(self):
        return self._word

    @property
    def added_letters(self):
        return self._added_letters

    @property
    def positions(self):
        return self._positions

    @property
    def is_valid(self):
        return self._is_valid

    def __str__(self):
        return self._word

    def check_beginning(self):
        length = len(self._word)
        if length < 4:
            return
        if length > 7:
            length = 7
        self._is_valid = is_in_group(self._word[:length])

    def check_end(self):
        length = len(self._word)
        if length < 4:
            return
        if length > 7:
            length = 7
        self._is_valid = is_in_group(self._word[-length:])

    def is_in_dictionary(self):
        return is_word_in_dictionary(self._word)

    def sort(self):
        self._added_letters.sort(key=lambda tup: tup[1])

    def create_child(self):
        return Word(self._rack, self._neighbours, self._word, self._points, self._multiplier, self._bonus,
                    self._positions[:],
                    self._added_letters[:])

    def generate_child(self, letter, position, extra_points, is_blank=False):
        child = self.create_child()
        child.add_letter(letter, position, extra_points, True, is_blank)
        if not child.is_valid:
            return None
        return child

    def generate_children(self, position):
        children = []
        neighbours = self._neighbours.get(position)
        for letter in set(self._rack):
            extra_points = 0
            if neighbours:
                if letter.lower() not in neighbours[0]:
                    continue
                extra_points = neighbours[1]
            if letter == BLANK:
                for new_letter in Sack.values_without_blank():
                    child = self.generate_child(new_letter, position, extra_points, True)
                    if child:
                        children.append(child)
            else:
                child = self.generate_child(letter, position, extra_points)
                if child:
                    children.append(child)
        return children

    def add_letter(self, letter, position, extra_points, is_from_rack, is_blank=False):
        if not self._word:
            self._word = letter
            self._positions.append(position)
        else:
            self._positions.append(position)
            self._positions.sort()
            index = self._positions.index(position)
            self._word = self._word[:index] + letter + self._word[index:]
            if index == 0:
                self.check_beginning()
            elif index == len(self._word) - 1:
                self.check_end()

        if not self.is_valid:
            return

        letter_points = Sack.get_value(letter)
        if is_blank:
            letter_points = 0

        if is_from_rack:
            self._added_letters.append((letter, letter_points, position))
            self._rack.remove(letter if letter_points else BLANK)

            if position in double_letter_bonus_coords:
                letter_points *= 2
            elif position in triple_letter_bonus_coords:
                letter_points *= 3
            elif position in double_word_bonus_coords:
                self._multiplier *= 2
            elif position in triple_word_bonus_coords:
                self._multiplier *= 3

        if extra_points:
            extra_points += letter_points
            if position in double_word_bonus_coords:
                extra_points *= 2
            elif position in triple_word_bonus_coords:
                extra_points *= 3
            self._bonus += extra_points

        self._points += letter_points

        if len(self._added_letters) == MAX_RACK_SIZE:
            self._bonus += 50

    def lower(self):
        return self._word.lower()

    def sum_up(self):
        return self._points * self._multiplier + self._bonus

    def possible_prefix(self, length=1):
        return possible_letters(length * BLANK + self._word)

    def possible_suffix(self, length=1):
        return possible_letters(self._word + length * BLANK)
