from sack import Sack
from copy import deepcopy
from board_utils import *
from dictionary import *


class Word:
    def __init__(self, rack, neighbours, word='', points=0, multiplier=1, positions=None, parent=None, start=None,
                 end=None, full_rack=False):
        self.word = word
        self.points = points
        self.multiplier = multiplier
        self.total_points = 0
        self.positions = positions if positions else []
        self.rack = rack[:]
        self.full_rack = False
        if len(rack) == 7 or full_rack:
            self.full_rack = True
        self.neighbours = neighbours
        self.parent = parent
        self.children = []
        self.is_in_dictionary = False
        self.is_valid = True
        self.start = start
        self.end = end

    def __str__(self):
        return self.word

    def check_beginning(self):
        if len(self.word) >= 4:
            self.is_valid = is_in_quads(self.word[:4])

    def check_end(self):
        if len(self.word) >= 4:
            self.is_valid = is_in_quads(self.word[-4:])

    def check_in_dictionary(self):
        self.is_in_dictionary = is_word_in_dictionary(self.word)

    def create_child(self):
        child = Word(self.rack, self.neighbours, self.word, self.points, self.multiplier, self.positions[:], self,
                     self.start, self.end, self.full_rack)
        self.children.append(child)
        return child

    def generate_child(self, letter, position, is_blank=False):
        child = self.create_child()
        child.add_letter(letter, position, True, is_blank)
        if not child.is_valid:
            return None
        child.check_in_dictionary()
        return child

    def generate_children(self, position):
        children = []
        neighbours = self.neighbours.get(position)
        for letter in set(self.rack):
            if neighbours is not None:
                if letter.lower() not in neighbours:
                    continue
            child = None
            if letter == '_':
                for new_letter in Sack.values_without_blank():
                    child = self.generate_child(new_letter, position, True)
                    if child:
                        children.append(child)
            else:
                child = self.generate_child(letter, position)
                if child:
                    children.append(child)
        return children

    def add_letter(self, letter, position, is_from_rack, is_blank=False):
        if not self.word:
            self.word = letter
            self.positions.append(position)
            self.start = self.end = position
        else:
            for index in range(len(self.word)):
                if compare_coords(position, self.positions[index]) == 1:
                    self.word = self.word[:index] + letter + self.word[index:]
                    self.positions.insert(index, position)
                    break
            else:
                self.word = self.word + letter
                self.positions.append(position)
        if self.start != self.positions[0]:
            self.start = self.positions[0]
            self.check_beginning()
        elif self.end != self.positions[-1]:
            self.end = self.positions[-1]
            self.check_end()

        if not self.is_valid:
            return

        letter_points = Sack.values.get(letter)
        if is_blank:
            letter_points = 0

        if is_from_rack:
            self.rack.remove('_' if is_blank else letter)
            if position in double_letter_bonus_coords:
                letter_points *= 2
            elif position in triple_letter_bonus_coords:
                letter_points *= 3
            elif position in double_word_bonus_coords:
                self.multiplier *= 2
            elif position in triple_word_bonus_coords:
                self.multiplier *= 3
        self.points += letter_points
        if self.full_rack and not self.rack:
            self.points += 50
        self.check_in_dictionary()

    def sum_up(self):
        self.total_points = self.points * self.multiplier

