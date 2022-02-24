import math
from threading import Thread
from time import sleep
from typing import List, Optional, Iterable, Dict, Tuple

from PyQt5.QtCore import QThread
from itertools import combinations

from board_utils import *
from constants import BLANK, MAX_RACK_SIZE, UP, DOWN, LEFT, RIGHT, DIRECTIONS
from dictionary import Dictionary
from heuristics import Heuristics
from sack import Sack
from tile import Tile
from vector import Vector
from word import Word


def variation_wor(k: int, n: int) -> int:
    result = 1
    for factor in range(n, n - k, -1):
        result *= factor
    return result


def sub_lists(super_list: List) -> List:
    lists = []
    for length in range(len(super_list)):
        lists.extend(set(combinations(super_list, length)))
    return lists


class AI(QThread):
    def __init__(self, tiles_from_player: Dict[Coords, Tile], sack: Sack) -> None:
        super().__init__()
        self.tiles_from_player = tiles_from_player
        self.sack = sack
        self.letters_remaining = Sack.get_all_letters()
        self.tiles_on_board = {}
        self.new_tiles = []

        self.word = None
        self.words_by_points = {}
        self.rack = self.sack.draw()

        for letter in self.rack:
            self.letters_remaining.remove(letter)

        self.horizontal_neighbours = {}
        self.vertical_neighbours = {}
        self.neighbours = {UP: self.horizontal_neighbours, DOWN: self.horizontal_neighbours,
                           LEFT: self.vertical_neighbours, RIGHT: self.vertical_neighbours}

        self.neighbourhoods = {}
        for direction in DIRECTIONS:
            self.neighbourhoods[direction] = {}

        self.turn_processes = []
        self.no_turn_processes = []

        self.is_turn = False
        self.current_turn = 0

    def add_new_tiles(self) -> None:
        self.new_tiles.clear()
        for tile_coords in self.tiles_from_player:
            self.new_tiles.append(tile_coords)
            letter, points = self.tiles_from_player.get(tile_coords).get_letter_and_points()
            self.tiles_on_board[tile_coords] = (letter, points)
            self.letters_remaining.remove(letter if points else BLANK)

    def find_sequence(self, direction: Vector, first_neighbour_coords: Coords, sequence: Optional[str] = '',
                      reversed_order: Optional[bool] = False):
        neighbour_coords = first_neighbour_coords
        points = 0
        while neighbour := self.tiles_on_board.get(neighbour_coords.move(direction)):
            sequence = neighbour[0] + sequence if reversed_order else sequence + neighbour[0]
            points += neighbour[1]
            neighbour_coords = neighbour_coords.move(direction)
        return sequence, neighbour_coords, points

    def find_closest_neighbourhood(self, tile_coords: Coords, direction: Vector) -> Optional[Coords]:
        neighbour = tile_coords.move(direction)
        while self.tiles_on_board.get(neighbour):
            neighbour = neighbour.move(direction)

        if neighbour.is_on_board():
            return neighbour
        return None

    def remove_neighbourhood(self, neighbour: Coords, direction: Vector) -> None:
        if self.neighbourhoods[direction].get(neighbour):
            del self.neighbourhoods[direction][neighbour]

    def remove_latest_from_neighbourhoods(self) -> None:
        for tile in self.new_tiles:
            for direction in DIRECTIONS:
                self.remove_neighbourhood(tile, direction)

    def add_neighbourhood(self, neighbourhood: Coords, direction: Vector, offset: int) -> None:
        if neighbourhood.move(direction).is_on_board():
            self.neighbourhoods[direction][neighbourhood] = (self.current_turn, offset)

    def add_neighbourhoods(self, coords: Coords, direction: Vector) -> None:
        offset = 1 if direction == abs(direction) else 0
        self.add_neighbourhood(coords, direction, offset)
        self.add_neighbourhood(coords, ~direction, offset + 1)
        self.add_neighbourhood(coords, -~direction, 2 - offset)

    def find_neighbours(self, tile_coords: Coords, direction: Vector,
                        neighbours: Dict[Coords, Tuple[List[str], int]]) -> None:
        start = ''
        middle, middle_points = self.tiles_on_board.get(tile_coords)
        end = ''

        neighbour = tile_coords
        middle, neighbour, points = self.find_sequence(-direction, neighbour, middle, True)
        middle_points += points

        previous_neighbour = neighbour.move(-direction)

        neighbour = neighbour.move(-direction)
        start, neighbour, start_points = self.find_sequence(-direction, neighbour, start, True)

        neighbour = tile_coords
        middle, neighbour, points = self.find_sequence(direction, neighbour, middle)
        middle_points += points

        next_neighbour = neighbour.move(direction)

        neighbour = neighbour.move(direction)
        end, neighbour, end_points = self.find_sequence(direction, neighbour, end)

        pre_pattern = start + BLANK + middle
        post_pattern = middle + BLANK + end

        neighbours[previous_neighbour] = (Dictionary.possible_letters(pre_pattern), start_points + middle_points)
        neighbours[next_neighbour] = (Dictionary.possible_letters(post_pattern), middle_points + end_points)

        self.add_neighbourhoods(previous_neighbour, -direction)
        self.add_neighbourhoods(next_neighbour, direction)

    def find_horizontal_neighbours(self, tile_coords: Coords) -> None:
        self.find_neighbours(tile_coords, RIGHT, self.horizontal_neighbours)

    def find_vertical_neighbours(self, tile_coords: Coords) -> None:
        self.find_neighbours(tile_coords, DOWN, self.vertical_neighbours)

    def fix_neighbourhoods(self) -> None:
        for direction in DIRECTIONS:
            for neighbourhood in sorted(self.neighbourhoods[direction]):
                if self.tiles_on_board.get(neighbourhood.move(direction)):
                    del self.neighbourhoods[direction][neighbourhood]

    def update_neighbourhoods(self) -> None:
        if not self.new_tiles:
            if len(self.tiles_on_board) == 0:
                neighbourhood = Coords.central()
                self.add_neighbourhood(neighbourhood, LEFT, 1)
                self.add_neighbourhood(neighbourhood, RIGHT, 2)
            return

        first_tile_coords = None
        for tile_coords in self.new_tiles:

            if tile_coords in self.vertical_neighbours:
                del self.vertical_neighbours[tile_coords]

            if tile_coords in self.vertical_neighbours:
                del self.vertical_neighbours[tile_coords]

            if not first_tile_coords:
                first_tile_coords = tile_coords
                self.find_horizontal_neighbours(tile_coords)
                self.find_vertical_neighbours(tile_coords)
            else:
                if first_tile_coords.is_same_column(tile_coords):
                    self.find_horizontal_neighbours(tile_coords)
                else:
                    self.find_vertical_neighbours(tile_coords)

        self.remove_latest_from_neighbourhoods()

    def add_word(self, word: Word) -> None:
        points = word.sum_up()
        if word.is_in_dictionary():
            if not self.words_by_points.get(points):
                self.words_by_points[points] = []
            self.words_by_points.get(points).append(word)

    def check_neighbourhood(self, coords: Coords, words: List[Word], direction: Vector) -> Coords:
        while True:
            coords = coords.move(direction)
            other_tile = self.tiles_on_board.get(coords)
            if not other_tile:
                return coords
            is_blank = other_tile[1] == 0
            for word in words[:]:
                word.add_letter(other_tile[0], coords, is_blank=is_blank)

    def find_words_with_direction(self, direction: Vector, new_neighbours_only: bool) -> None:
        tiles = self.tiles_on_board
        rack = self.rack
        neighbourhoods = self.neighbourhoods[direction]
        neighbours = self.neighbours[direction]
        current_turn = self.current_turn

        for current in neighbourhoods:
            turn, offset = neighbourhoods.get(current)
            if new_neighbours_only and turn != current_turn:
                continue

            previous_main_words = [Word(rack)]
            first_neighbourhood = self.check_neighbourhood(current, previous_main_words, -direction)

            for letters_in_direction in range(1, len(rack) + 1):
                current_words = []
                for word in previous_main_words:
                    current_words.extend(word.generate_children(current, neighbours.get(current)))

                if not current_words:
                    break

                next_neighbourhood = current.move(direction)
                if tiles.get(next_neighbourhood):
                    next_neighbourhood = self.check_neighbourhood(current, current_words, direction)

                for word in current_words:
                    self.add_word(word)

                previous_main_words = current_words
                previous_side_words = current_words[:]

                previous_neighbourhood = first_neighbourhood

                max_letters_in_opposite_direction = letters_in_direction - offset
                if max_letters_in_opposite_direction + letters_in_direction > len(rack):
                    max_letters_in_opposite_direction = len(rack) - letters_in_direction

                for letters_in_opposite_direction in range(1, max_letters_in_opposite_direction + 1):
                    if not previous_neighbourhood.is_on_board():
                        break

                    current = previous_neighbourhood

                    current_words = []

                    for word in previous_side_words:
                        current_words.extend(word.generate_children(current, neighbours.get(current)))

                    if not current_words:
                        break

                    previous_neighbourhood = current.move(-direction)
                    if tiles.get(previous_neighbourhood):
                        previous_neighbourhood = self.check_neighbourhood(current, current_words,
                                                                          -direction)

                    for word in current_words:
                        self.add_word(word)

                    previous_side_words = current_words

                if not next_neighbourhood.is_on_board():
                    break
                current = next_neighbourhood

    def find_new_words(self, new_neighbours_only: Optional[bool] = False) -> None:
        threads = []
        for direction in DIRECTIONS:
            threads.append(
                Thread(target=self.find_words_with_direction, args=(direction, new_neighbours_only,)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def evaluate_closest_word_bonus(self, coords: Coords, direction: Vector,
                                    is_neighbourhood: Optional[bool] = False) -> float:
        if not is_neighbourhood:
            coords = coords.move(direction)


        distance = 1
        possibility = 1
        bonus = 1

        while coords.is_on_board() and distance <= MAX_RACK_SIZE:
            if self.tiles_on_board.get(coords):
                coords = coords.move(direction)
                continue

            elif neighbours := self.neighbours[direction].get(coords):
                possibility *= self.calculate_expandability(neighbours[0])

            if coords in double_word_bonuses:
                bonus = 3
                break
            elif coords in triple_word_bonuses:
                bonus = 2
                break
            coords = coords.move(direction)
            distance += 1

        if bonus != 1:
            evaluation = -bonus * possibility
            if distance > 1:
                evaluation *= (pow(12 - distance, 2) - 10) / 200
        else:
            evaluation = 0

        return evaluation

    def count_letters(self, letters_to_count: Iterable[str]) -> int:
        count = 0
        for letter in letters_to_count:
            count += self.letters_remaining.count(letter)

        if letters_to_count:
            count += self.letters_remaining.count(BLANK)

        return count

    def calculate_expandability(self, letters: List[str]) -> float:
        letters_count = self.count_letters(letters)
        how_many_remaining = len(self.letters_remaining)
        if how_many_remaining < MAX_RACK_SIZE:
            return 1 if letters_count else 0

        return 1 - variation_wor(
            MAX_RACK_SIZE, how_many_remaining - letters_count) / variation_wor(
            MAX_RACK_SIZE, how_many_remaining)

    @staticmethod
    def points_for_letters(letters: Iterable[str]) -> int:
        points = 0
        for letter in letters:
            points += Sack.get_value(letter)

        return points

    def evaluate_remaining_letters(self, letters: List[str]) -> float:
        evaluation_points = 0
        vowels = consonants = blanks = 0
        evaluated_letters = []

        for letter in letters:
            if letter in Dictionary.vowels:
                vowels += 1
            elif letter in Dictionary.consonants:
                consonants += 1
            else:
                blanks += 1
            evaluation_points += Heuristics.evaluate_first_letter(letter)
            if letter in evaluated_letters:
                evaluation_points += evaluated_letters.count(letter) * Heuristics.evaluate_another_letter(letter)

            evaluated_letters.append(letter)

        evaluation_points += Heuristics.check_pairs(letters)

        if self.sack.is_empty():
            if not letters:
                evaluation_points += self.points_for_letters(self.letters_remaining)
            else:
                evaluation_points -= blanks * Heuristics.evaluate_first_letter(BLANK)

        evaluation_points += Heuristics.evaluate_vowels_and_consonants(vowels, consonants)

        return evaluation_points

    def evaluate_prefix_expandability(self, word: Word) -> float:
        prefixes = word.possible_prefix()
        expandability = self.calculate_expandability(prefixes)

        worst_evaluation = 0

        for direction in [~word.direction(), ~-word.direction()]:
            evaluation = self.evaluate_closest_word_bonus(word.start.move(-word.direction()),
                                                          direction, True)
            if evaluation < worst_evaluation:
                worst_evaluation = evaluation

        return worst_evaluation * expandability

    def evaluate_suffix_expandability(self, word: Word) -> float:
        suffixes = word.possible_suffix()
        expandability = self.calculate_expandability(suffixes)
        worst_evaluation = 0

        for direction in [~word.direction(), ~-word.direction()]:
            evaluation = self.evaluate_closest_word_bonus(word.end.move(word.direction()),
                                                          direction, True)

            if evaluation < worst_evaluation:
                worst_evaluation = evaluation

        return worst_evaluation * expandability

    def evaluate_expandability(self, word: Word) -> float:
        prefix_expandability = self.evaluate_prefix_expandability(word)
        suffix_expandability = self.evaluate_suffix_expandability(word)
        return min(prefix_expandability, suffix_expandability) * self.points_for_letters(word.word) / 3

    def evaluate_word(self, word: Word) -> float:
        word_points = word.sum_up()

        remaining_letters_points = self.evaluate_remaining_letters(word.rack)

        expandability_points = self.evaluate_expandability(word)

        evaluation_points = word_points + remaining_letters_points + expandability_points

        return evaluation_points

    def remove_invalid_words(self) -> None:
        coords_to_check = set(self.new_tiles)
        for direction in DIRECTIONS:
            for neighbourhood in self.neighbourhoods[direction]:
                turn, _ = self.neighbourhoods[direction].get(neighbourhood)
                if turn == self.current_turn:
                    coords_to_check.add(neighbourhood)

        for words in self.words_by_points.values():
            for word in words[:]:
                if not coords_to_check.isdisjoint(word.added_letters.keys()):
                    words.remove(word)

    def exchange_letters(self) -> None:
        best_sub_rack = None
        best_sub_rack_evaluation = -100

        remaining_letters = self.sack.how_many_remain()
        for sub_rack in sub_lists(self.rack):
            if remaining_letters < MAX_RACK_SIZE - len(sub_rack):
                continue
            sub_rack_evaluation = self.evaluate_remaining_letters(sub_rack)
            if sub_rack_evaluation > best_sub_rack_evaluation:
                best_sub_rack_evaluation = sub_rack_evaluation
                best_sub_rack = sub_rack

        if best_sub_rack:
            new_letters = self.sack.exchange([letter for letter in self.rack if letter not in best_sub_rack])
            self.rack = list(best_sub_rack) + new_letters

    def place_word(self) -> None:
        self.new_tiles.clear()
        for coords in self.word.added_letters:
            letter, points = self.word.added_letters.get(coords)
            self.rack.remove(letter if points else BLANK)
            self.tiles_on_board[coords] = (letter, points)
            self.new_tiles.append(coords)

    # I start no_turn after my move when player is thinking
    def no_turn(self) -> None:
        # I search for neighbourhood and neighbours around placed word
        self.update_neighbourhoods()
        # I remove invalid neighbourhoods
        self.fix_neighbourhoods()
        # I look for words on whole board
        self.find_new_words()
        # I allow myself to start turn

    # I start turn after finishing no_turn if player has placed his word
    def turn(self) -> None:
        # I wait for player to finish
        while not self.is_turn:
            sleep(0.1)
        self.current_turn += 1
        # I include tiles that players have added
        self.add_new_tiles()
        # I search for neighbourhood and neighbours around player's word
        self.update_neighbourhoods()
        # I remove these words I found in no_turn which interfere with new tiles
        self.remove_invalid_words()
        # I look for words around new tiles
        self.find_new_words(True)

    def end_turn(self) -> None:
        # I forgot previous word
        self.word = None
        best_evaluation_points = -100

        # I evaluate words, looking for the best
        for words in self.words_by_points.values():
            for word in words:
                evaluation_points = self.evaluate_word(word)
                if evaluation_points > best_evaluation_points:
                    self.word = word
                    best_evaluation_points = evaluation_points
            words.clear()
        self.words_by_points.clear()

        if not self.word:
            self.exchange_letters()
        else:
            # I accept chosen word
            self.place_word()
        self.finished.emit()

        self.is_turn = False
        new_letters = self.sack.draw(MAX_RACK_SIZE - len(self.rack))
        if new_letters:
            for letter in new_letters:
                self.letters_remaining.remove(letter)
            self.rack.extend(new_letters)

        # I forget every word I found
        self.words_by_points.clear()

    def run(self):
        while True:
            self.turn()
            self.end_turn()
            self.no_turn()

    def stop(self):
        self.terminate()
