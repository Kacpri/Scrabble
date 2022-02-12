from PyQt5.QtCore import QThread
from multiprocessing import Manager, Process
from time import sleep

from sack import Sack
from board_utils import *
from dictionary import Dictionary
from constants import BLANK, MAX_RACK_SIZE, UP, DOWN, LEFT, RIGHT, DIRECTIONS
from word import Word


def wait_for_processes(processes):
    for process in processes:
        process.join()
    processes.clear()


def variation_wor(k, n):
    result = 1
    for factor in range(n, n - k, -1):
        result *= factor
    return result


class AI(QThread):
    @staticmethod
    def add_word(words_dict, word, key_function):
        if word.is_in_dictionary():
            points = key_function(word)
            if not words_dict.get(points):
                words_dict[points] = []
            words_dict.get(points).append(word)

    @staticmethod
    def check_neighbourhood(tiles_list, coords, words, direction):
        while True:
            coords = coords.move(direction)
            other_tile = tiles_list.get(coords)
            if not other_tile:
                return coords
            is_blank = other_tile[1] == 0
            for word in words[:]:
                word.add_letter(other_tile[0], coords, 0, False, is_blank)
                if not word.is_valid:
                    words.remove(word)

    @classmethod
    def find_words_with_direction(cls, tiles_on_board, rack, direction, neighbourhoods_to_check, neighbours, words):
        words_by_points = {}
        for current in neighbourhoods_to_check:
            offset = neighbourhoods_to_check.get(current)
            all_words = [[] for _ in range(9)]
            first_word = Word(rack, abs(direction), neighbours)
            first_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, [first_word], -direction)
            all_words[0] = [first_word]
            for direct_level in range(1, len(rack) + 1):
                all_words[direct_level] = []
                for word in all_words[direct_level - 1]:
                    all_words[direct_level].extend(word.generate_children(current))
                all_words[direct_level - 1].clear()
                if not all_words[direct_level]:
                    break

                next_neighbour_coords = first_neighbour_coords
                previous_neighbour_coords = current.move(direction)
                if previous_neighbour_coords.is_on_board() and tiles_on_board.get(previous_neighbour_coords):
                    previous_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current,
                                                                        all_words[direct_level], direction)
                for word in all_words[direct_level]:
                    cls.add_word(words_by_points, word, Word.sum_up)

                stop_value = direct_level - offset
                if direct_level > len(rack) / 2:
                    stop_value = len(rack) - direct_level
                for opposite_level in range(stop_value):
                    if not next_neighbour_coords.is_on_board():
                        break
                    current = next_neighbour_coords
                    level = direct_level + opposite_level + 1
                    all_words[level] = []

                    for word in all_words[level - 1]:
                        all_words[level].extend(word.generate_children(current))

                    if opposite_level > 0:
                        all_words[level - 1].clear()

                    next_neighbour_coords = current.move(-direction)

                    if tiles_on_board.get(next_neighbour_coords):
                        next_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, all_words[level],
                                                                        -direction)

                    for word in all_words[level]:
                        cls.add_word(words_by_points, word, Word.sum_up)

                if not previous_neighbour_coords.is_on_board():
                    break
                current = previous_neighbour_coords

        if not words_by_points:
            return

        max_points = max(words_by_points)
        for points in sorted(words_by_points, reverse=True):
            if points < max_points / 2:
                return
            for word in words_by_points.get(points):
                words.append(word)

    def __init__(self, tiles_from_player, sack):
        super().__init__()
        self.tiles_from_player = tiles_from_player
        self.sack = sack
        self.letters_remaining = Sack.get_all_letters()
        self.tiles_on_board = {}
        self.new_tiles = None

        self.word = None
        self.chosen_words = None
        self.manager = Manager()
        self.no_turn_words = self.manager.list()
        self.turn_words = self.manager.list()
        self.words_by_points = {}
        self.rack = self.sack.draw()

        for letter in self.rack:
            self.letters_remaining.remove(letter)

        self.horizontal_neighbours = {}
        self.vertical_neighbours = {}
        self.neighbours = {UP: self.horizontal_neighbours, DOWN: self.horizontal_neighbours,
                           LEFT: self.vertical_neighbours, RIGHT: self.vertical_neighbours}

        self.neighbourhoods_to_check = {}
        self.new_neighbourhoods_to_check = {}
        for direction in DIRECTIONS:
            self.neighbourhoods_to_check[direction] = {}
            self.new_neighbourhoods_to_check[direction] = {}

        self.turn_processes = []
        self.no_turn_processes = []

        self.is_turn = False

    def add_new_tiles(self):
        self.new_tiles = []
        for tile_coords in self.tiles_from_player:
            self.new_tiles.append(tile_coords)
            letter, points = self.tiles_from_player.get(tile_coords).get_letter_and_points()
            self.tiles_on_board[tile_coords] = (letter, points)
            self.letters_remaining.remove(letter if points else BLANK)

    def remove_neighbourhood_to_check(self, neighbour, direction):
        if self.neighbourhoods_to_check[direction].get(neighbour):
            del self.neighbourhoods_to_check[direction][neighbour]

    def remove_latest_from_neighbourhoods(self):
        for tile in self.new_tiles:
            for direction in DIRECTIONS:
                self.remove_neighbourhood_to_check(tile, direction)

    def find_sequence(self, direction, first_neighbour_coords, sequence='', reversed_order=False):
        neighbour_coords = first_neighbour_coords
        points = 0
        while neighbour := self.tiles_on_board.get(neighbour_coords.move(direction)):
            sequence = neighbour[0] + sequence if reversed_order else sequence + neighbour[0]
            points += neighbour[1]
            neighbour_coords = neighbour_coords.move(direction)
        return sequence, neighbour_coords, points

    def find_closest_neighbourhood(self, tile_coords, direction):
        neighbour = tile_coords.move(direction)
        while self.tiles_on_board.get(neighbour):
            neighbour = neighbour.move(direction)

        if neighbour.is_on_board():
            return neighbour
        return None

    def add_neighbourhood(self, neighbourhood, direction, offset=0):
        self.neighbourhoods_to_check[direction][neighbourhood] = offset
        self.new_neighbourhoods_to_check[direction][neighbourhood] = offset

    def add_neighbourhoods(self, coords, direction):
        offset = 1 if direction == abs(direction) else 0
        self.add_neighbourhood(coords, direction, offset)
        self.add_neighbourhood(coords, ~direction, offset + 1)
        self.add_neighbourhood(coords, -~direction, 2 - offset)

    def find_neighbours(self, tile_coords, direction, neighbours):
        start = ""
        middle, middle_points = self.tiles_on_board.get(tile_coords)
        end = ""

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(-direction, neighbour_coords, middle, True)
        middle_points += points

        previous_neighbour_coords = neighbour_coords.move(-direction)

        neighbour_coords = neighbour_coords.move(-direction)
        start, neighbour_coords, start_points = self.find_sequence(-direction, neighbour_coords, start, True)

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(direction, neighbour_coords, middle)
        middle_points += points

        next_neighbour_coords = neighbour_coords.move(direction)

        neighbour_coords = neighbour_coords.move(direction)
        end, neighbour_coords, end_points = self.find_sequence(direction, neighbour_coords, end)

        self.add_neighbourhoods(previous_neighbour_coords, -direction)
        self.add_neighbourhoods(next_neighbour_coords, direction)

        pre_pattern = start + BLANK + middle
        post_pattern = middle + BLANK + end

        neighbours[previous_neighbour_coords] = (Dictionary.possible_letters(pre_pattern), start_points + middle_points)
        neighbours[next_neighbour_coords] = (Dictionary.possible_letters(post_pattern), middle_points + end_points)

    def find_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, RIGHT, self.horizontal_neighbours)

    def find_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, DOWN, self.vertical_neighbours)

    def fix_neighbourhoods(self):
        for direction in DIRECTIONS:
            for neighbourhood in sorted(self.neighbourhoods_to_check[direction]):
                if self.tiles_on_board.get(neighbourhood.move(direction)):
                    del self.neighbourhoods_to_check[direction][neighbourhood]

    def update_neighbourhoods(self):
        if not self.new_tiles:
            if len(self.tiles_on_board) == 0:
                neighbourhood = Coords.central()
                self.add_neighbourhood(neighbourhood, LEFT, 1)
                self.add_neighbourhood(neighbourhood, RIGHT, 2)
            return

        for direction in DIRECTIONS:
            self.new_neighbourhoods_to_check[direction].clear()

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
        self.fix_neighbourhoods()

    def find_new_words(self, neighbourhoods_to_check, words, processes):
        for direction in DIRECTIONS:
            process = Process(target=AI.find_words_with_direction,
                              args=(self.tiles_on_board, self.rack, direction, neighbourhoods_to_check[direction],
                                    self.neighbours[direction], words))
            processes.append(process)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def closest_word_bonus(self, coords, direction, start_here=False, is_important=False):
        if not start_here:
            coords = coords.move(direction)
        tiles_count = 0
        distance = 1
        letters_behind = ''
        possibility = 1

        while coords.is_valid() and distance <= 7:
            if tile := self.tiles_on_board.get(coords):
                if not is_important:
                    return 1
                letters_behind += tile.letter
            else:
                letters_behind += BLANK

            if coords in self.neighbours[direction]:
                if not is_important:
                    return 1
                possibility *= self.calculate_expandability(self.neighbours[direction].get(coords)[0])
            if coords in double_word_bonus_coords:
                bonus = 2
                break
            elif coords in triple_word_bonus_coords:
                bonus = 3
                break
            coords = coords.move(direction)
            distance += 1
        else:
            return 1

        coords = coords.move(direction)
        while tile := self.tiles_on_board.get(coords):
            letter, _ = tile
            # tiles_behind += letter
            coords = coords.move(direction)

        return 1
        # return distance, bonus, tiles_behind

    def count_letters(self, letters_to_count):
        count = 0
        for letter in letters_to_count:
            count += self.letters_remaining.count(letter)

        if count:
            count += self.letters_remaining.count(BLANK)

        return count

    def calculate_expandability(self, letters):
        letters_count = self.count_letters(letters)
        how_many_remaining = len(self.letters_remaining)
        if how_many_remaining < MAX_RACK_SIZE:
            return 1 if letters_count else 0

        return 1 - variation_wor(MAX_RACK_SIZE, how_many_remaining - letters_count) / variation_wor(MAX_RACK_SIZE,
                                                                                                    how_many_remaining)

    def evaluate_word(self, word):
        evaluation_points = 0

        # How many points is the word worth
        word_points = word.sum_up()
        if self.word and word_points < self.word.evaluation_points:
            return

        # How many points are letters the word worth
        points_for_letters = 0
        # How many blanks does the word contain
        blanks_in_word = 0
        # What is the direction of the word

        blanks_remaining = self.letters_remaining.count(BLANK)

        first_coords = min(word.positions)
        last_coords = max(word.positions)

        # neighbourhood_of_first = first_coords.move.word.direction.perpendicular()
        # if not tiles.get(neighbourhood_of_first):
        #
        #     for coords in neighbours:
        #         pass
        #     bonus = AI.closest_word_bonus()
        # first_coords.move.word.direction.perpendicular().opposite()
        # bonus = AI.closest_word_bonus(first_coords.move.word.direction.perpendicular(),
        #                               word.direction.opposite(), tiles)

        for coords in word.added_letters:
            letter, points = word.added_letters.get(coords)
            points_for_letters += points
            if points == 0:
                blanks_in_word += 1

        # bonus = AI.closest_word_bonus(coords, word.direction, tiles)

        letters_factor = word_points
        if blanks_in_word and len(self.letters_remaining) - len(word.word) > MAX_RACK_SIZE:
            letters_factor -= 50 - points_for_letters

        if letters_factor < 0:
            return

        letters_factor /= points_for_letters * 2
        if letters_factor > 1:
            letters_factor = 1

        pre_expandability = self.calculate_expandability(word.possible_prefix())
        sub_expandability = self.calculate_expandability(word.possible_suffix())
        # pre_expandability = self.calculate_expandability(word.possible_prefix()) * self.closest_word_bonus(
        #     first_coords.move(-word.direction), -word.direction, True, True)
        # sub_expandability = self.calculate_expandability(word.possible_suffix()) * self.closest_word_bonus(
        #     last_coords.move(word.direction), word.direction, True, True)
        expandability = max([pre_expandability, sub_expandability])

        evaluation_points = word_points * letters_factor * (1 - expandability / 2)

        print(word, word_points, letters_factor, expandability, evaluation_points)

        if not self.word or evaluation_points > self.word.evaluation_points:
            self.word = word
            word.evaluation_points = evaluation_points

    def find_best_valid_words(self, words):
        coords_to_check = set(self.new_tiles)
        for direction in DIRECTIONS:
            coords_to_check.update(list(self.new_neighbourhoods_to_check[direction]))
        while words:
            word = words.pop()
            if coords_to_check.isdisjoint(word.positions):
                self.evaluate_word(word)

    def place_word(self):
        self.new_tiles = []
        for coords in self.word.added_letters:
            letter, points = self.word.added_letters.get(coords)
            self.rack.remove(letter if points else BLANK)
            self.tiles_on_board[coords] = (letter, points)
            self.new_tiles.append(coords)

    # I start no_turn after my move when player is thinking
    def no_turn(self):
        # I search for neighbours around placed word
        self.update_neighbourhoods()
        # I look for words
        self.find_new_words(self.neighbourhoods_to_check, self.no_turn_words, self.no_turn_processes)
        # I allow myself to start turn

    # I start turn after finishing no_turn if player has placed his word
    def turn(self):
        # I wait for player to finish
        while not self.is_turn:
            sleep(0.1)

        self.add_new_tiles()

        self.update_neighbourhoods()

        self.find_new_words(self.new_neighbourhoods_to_check, self.turn_words, self.turn_processes)

    def end_turn(self):
        wait_for_processes(self.no_turn_processes)

        self.word = None
        self.find_best_valid_words(self.no_turn_words)

        wait_for_processes(self.turn_processes)

        while self.turn_words:
            word = self.turn_words.pop()
            self.evaluate_word(word)

        if not self.word:
            # exchange letters here or wait
            return

        self.place_word()

        self.is_turn = False
        self.finished.emit()

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
