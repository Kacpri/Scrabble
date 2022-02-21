from typing import List

from constants import BLANK


class Heuristics:
    _first_letter_heuristics = {
        'a': 2, 'e': 0, 'i': 1, 'n': -0.5, 'o': 1, 'r': 0, 's': -1, 'w': -1, 'z': -0.5, 'c': 1.5, 'd': 0, 'k': 2.5,
        'l': 0, 'm': 2, 'p': 0.5, 't': 0.5, 'y': 1, 'b': -1, 'g': -1.5, 'h': -4, 'j': -0.5, 'ł': 0.5, 'u': 2, 'ą': 1.5,
        'ę': 0.5, 'f': -2, 'ó': -1, 'ś': -1.5, 'ż': 2, 'ć': -2.5, 'ń': -1.5, 'ź': -7, BLANK: 25}

    _second_letter_heuristics = {
        'a': -1, 'e': -1.5, 'i': -2, 'n': -1.5, 'o': -1, 'r': -5, 's': -4, 'w': -3.5, 'z': -1.5, 'c': -2, 'd': -5,
        'k': -3, 'l': -4.5, 'm': -3, 'p': -4, 't': -3.5, 'y': -3, 'b': -5, 'g': -7, 'h': -10, 'j': -9, 'ł': -6, 'u': -5,
        BLANK: -15}

    _pairs = [
        ({'c', 'h'}, 4), ({'s', 'z'}, 2.5), ({'c', 'z'}, 2), ({'r', 'z'}, 1.5), ({'d', 'z'}, 0.5), ({'d', 'ź'}, 5),
        ({'ó', 'w'}, 3), ({'ć', 'ś'}, 1.5)
    ]

    _vowel_and_consonant_heuristics = [
        [0, 0, -1, -2, -3, -4, -5],
        [-1, 1, 1, 0, -1, -2],
        [-2, 0, 2, 2, 1],
        [-3, -1, 1, 3],
        [-4, -2, 0],
        [-5, -3],
        [-6]

    ]

    @classmethod
    def evaluate_first_letter(cls, letter: str) -> int:
        return cls._first_letter_heuristics.get(letter)

    @classmethod
    def evaluate_another_letter(cls, letter: str) -> int:
        return cls._second_letter_heuristics.get(letter)

    @classmethod
    def evaluate_vowels_and_consonants(cls, vowels_count: int, consonants_count: int) -> int:
        return cls._vowel_and_consonant_heuristics[vowels_count][consonants_count]

    @classmethod
    def check_pairs(cls, letters: List[str]) -> int:
        total_points = 0
        letters = set(letters)
        for pair, points in cls._pairs:
            if pair.issubset(letters):
                total_points += points

        return total_points
