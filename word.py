from board_utils import *
from dictionary import *


class Word:
    def __init__(self, rack, neighbours, word='', points=0, multiplier=1, bonus=0, positions=None, parent=None,
                 start=None, end=None, added_letters=None, blanks=None):
        if not positions:
            positions = []
        if not added_letters:
            added_letters = []
        if not blanks:
            blanks = []
        self.word = word
        self.points = points
        self.multiplier = multiplier
        self.bonus = bonus
        self.positions = positions
        self.added_letters = added_letters
        self.blanks = blanks
        self.rack = rack[:]
        self.neighbours = neighbours
        self.parent = parent
        self.children = []
        self.is_valid = True
        self.start = start
        self.end = end

    def __str__(self):
        return self.word

    def check_beginning(self):
        length = len(self.word)
        if length < 4:
            return
        if length > 7:
            length = 7
        self.is_valid = is_in_group(self.word[:length], length)

    def check_end(self):
        length = len(self.word)
        if length < 4:
            return
        if length > 7:
            length = 7
        self.is_valid = is_in_group(self.word[-length:], length)

    def is_in_dictionary(self):
        return is_word_in_dictionary(self.word)

    def create_child(self):
        child = Word(self.rack, self.neighbours, self.word, self.points, self.multiplier, self.bonus, self.positions[:],
                     self, self.start, self.end, self.added_letters[:], self.blanks[:])
        self.children.append(child)
        return child

    def generate_child(self, letter, position, extra_points, is_blank=False):
        child = self.create_child()
        child.add_letter(letter, position, extra_points, True, is_blank)
        if not child.is_valid:
            return None
        return child

    def generate_children(self, position):
        children = []
        neighbours = self.neighbours.get(position)
        for letter in set(self.rack):
            extra_points = 0
            if neighbours:
                if letter.lower() not in neighbours[0]:
                    continue
                extra_points = neighbours[1]
            if letter == BLANK:
                for new_letter in Sack.values_without_blank():
                    if new_letter in self.rack:
                        continue
                    child = self.generate_child(new_letter, position, extra_points, True)
                    if child:
                        children.append(child)
            else:
                child = self.generate_child(letter, position, extra_points)
                if child:
                    children.append(child)
        return children

    def add_letter(self, letter, position, extra_points, is_from_rack, is_blank=False):
        if not self.word:
            self.word = letter
            self.positions.append(position)
            self.start = self.end = position
        else:
            for index in range(len(self.word)):
                if position < self.positions[index]:
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
            self.added_letters.append(letter)
            if is_blank:
                self.rack.remove(BLANK)
                self.blanks.append(position)
            else:
                self.rack.remove(letter)
            if position in double_letter_bonus_coords:
                letter_points *= 2
            elif position in triple_letter_bonus_coords:
                letter_points *= 3
            elif position in double_word_bonus_coords:
                self.multiplier *= 2
            elif position in triple_word_bonus_coords:
                self.multiplier *= 3

        if extra_points:
            extra_points += letter_points
            if position in double_word_bonus_coords:
                extra_points *= 2
            elif position in triple_word_bonus_coords:
                extra_points *= 3
            self.bonus += extra_points

        self.points += letter_points

        if len(self.added_letters) == 7:
            self.bonus += 50

    def sum_up(self):
        return self.points * self.multiplier + self.bonus
