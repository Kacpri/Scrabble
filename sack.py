from random import sample, choice
from constants import BLANK, MAX_RACK_SIZE


class Sack:
    _values = {'A': 1, 'E': 1, 'I': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'W': 1, 'Z': 1, 'C': 2, 'D': 2, 'K': 2,
               'L': 2, 'M': 2, 'P': 2, 'T': 2, 'Y': 2, 'B': 3, 'G': 3, 'H': 3, 'J': 3, 'Ł': 3, 'U': 3, 'Ą': 5, 'Ę': 5,
               'F': 5, 'Ó': 5, 'Ś': 5, 'Ż': 5, 'Ć': 6, 'Ń': 7, 'Ź': 9, BLANK: 0}

    _all_letters = ['A'] * 9 + ['I'] * 8 + ['E'] * 7 + ['O'] * 6 + ['N', 'Z'] * 5 + ['R', 'S', 'W', 'Y'] * 4 + \
                   ['C', 'D', 'K', 'L', 'M', 'P', 'T'] * 3 + ['B', 'D', 'H', 'J', 'Ł', 'U', BLANK] * 2 + \
                   ['Ą', 'Ę', 'Ć', 'F', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż']

    @classmethod
    def get_all_letters(cls):
        return cls._all_letters

    @classmethod
    def get_value(cls, value):
        return cls._values.get(value)

    @classmethod
    def values_without_blank(cls):
        return list(cls._values)[:-1]

    def __init__(self, label=None):
        self._letters = Sack._all_letters[:]

        self.label = label

    def draw(self, quantity=MAX_RACK_SIZE):
        if not self._letters:
            return None
        elif len(self._letters) < quantity:
            quantity = len(self._letters)

        drawn = sample(self._letters, quantity)
        self.remove_letters(drawn)

        return drawn

    def draw_one(self):
        if not self._letters:
            return None

        drawn = choice(self._letters)
        self._letters.remove(drawn)
        self.update_label()

        return drawn

    def remove_letters(self, letters_to_remove):
        for letter in letters_to_remove:
            self._letters.remove(letter)
        self.update_label()

    def return_letters(self, letters):
        for letter in letters:
            self._letters.append(letter)
        self.update_label()

    def exchange(self, letters_to_exchange):
        if len(letters_to_exchange) > len(self._letters):
            return None
        drawn = self.draw(len(letters_to_exchange))
        self.return_letters(letters_to_exchange)
        return drawn

    def how_many_remain(self):
        return len(self._letters)

    def update_label(self):
        if self.label:
            self.label.setText(str(len(self._letters)))
