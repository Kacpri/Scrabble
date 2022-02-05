from PyQt5.QtCore import QThread
from multiprocessing import Manager, Process
from time import sleep

from board_utils import *
from dictionary import Dictionary
from constants import BLANK, MAX_RACK_SIZE
from direction import Direction
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
            coords = direction(coords)
            neighbourhood = tiles_list.get(coords)
            if not neighbourhood:
                return coords
            is_blank = neighbourhood[1] == 0
            for word in words:
                word.add_letter(neighbourhood[0], coords, 0, False, is_blank)

    @classmethod
    def find_new_word_with_direction(cls, tiles_on_board, rack, direction, neighbourhoods_to_check, neighbours, words):
        words_by_points = {}
        direct_coords, opposite_coords = Coords.get_functions(direction)
        for current in neighbourhoods_to_check:
            offset, max_opposite_length = neighbourhoods_to_check.get(current)
            all_words = [[] for _ in range(9)]
            first_word = Word(rack, direction.bivalent(), neighbours)
            first_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, [first_word], opposite_coords)
            all_words[0] = [first_word]
            for direct_level in range(1, len(rack) + 1):
                all_words[direct_level] = []
                for word in all_words[direct_level - 1]:
                    all_words[direct_level].extend(word.generate_children(current))
                all_words[direct_level - 1].clear()
                if not all_words[direct_level]:
                    break

                next_neighbour_coords = first_neighbour_coords
                previous_neighbour_coords = direct_coords(current)
                if previous_neighbour_coords.is_on_board() and tiles_on_board.get(previous_neighbour_coords):
                    previous_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current,
                                                                        all_words[direct_level], direct_coords)
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

                    next_neighbour_coords = opposite_coords(current)

                    if tiles_on_board.get(next_neighbour_coords):
                        next_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, all_words[level],
                                                                        opposite_coords)

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
        self.letters_remaining = ['A'] * 9 + ['I'] * 8 + ['E'] * 7 + ['O'] * 6 + ['N', 'Z'] * 5 + \
                                 ['R', 'S', 'W', 'Y'] * 4 + ['C', 'D', 'K', 'L', 'M', 'P', 'T'] * 3 + \
                                 ['B', 'D', 'H', 'J', 'Ł', 'U', BLANK] * 2 + \
                                 ['Ą', 'Ę', 'Ć', 'F', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż']
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

        horizontal = {}
        vertical = {}
        self.neighbours = {Direction.UP: vertical, Direction.DOWN: vertical,
                           Direction.LEFT: horizontal, Direction.RIGHT: horizontal}

        self.neighbourhoods_to_check = {}
        self.new_neighbourhoods_to_check = {}
        for direction in Direction:
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
            for direction in Direction:
                self.remove_neighbourhood_to_check(tile, direction)

    def find_sequence(self, direction, first_neighbour_coords, sequence='', reversed_order=False):
        neighbour_coords = first_neighbour_coords
        points = 0
        while neighbour := self.tiles_on_board.get(direction(neighbour_coords)):
            sequence = neighbour[0] + sequence if reversed_order else sequence + neighbour[0]
            points += neighbour[1]
            neighbour_coords = direction(neighbour_coords)
        return sequence, neighbour_coords, points

    def find_closest_neighbourhood(self, tile_coords, direction):
        direct_coords, _ = Coords.get_functions(direction)
        neighbour = direct_coords(tile_coords)
        while self.tiles_on_board.get(neighbour):
            neighbour = direct_coords(neighbour)

        if neighbour.is_on_board():
            return neighbour
        return None

    def find_neighbours(self, tile_coords, direction, neighbours):
        direct_coords, opposite_coords = Coords.get_functions(direction)

        start = ""
        middle, middle_points = self.tiles_on_board.get(tile_coords)
        end = ""

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(direct_coords, neighbour_coords, middle, True)
        middle_points += points

        previous_neighbour_coords = direct_coords(neighbour_coords)

        neighbour_coords = direct_coords(neighbour_coords)
        start, neighbour_coords, start_points = self.find_sequence(direct_coords, neighbour_coords, start, True)

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(opposite_coords, neighbour_coords, middle)
        middle_points += points

        next_neighbour_coords = opposite_coords(neighbour_coords)

        neighbour_coords = opposite_coords(neighbour_coords)
        end, neighbour_coords, end_points = self.find_sequence(opposite_coords, neighbour_coords, end)

        pre_pattern = start + BLANK + middle
        post_pattern = middle + BLANK + end

        neighbours[previous_neighbour_coords] = (Dictionary.possible_letters(pre_pattern), start_points + middle_points)
        neighbours[next_neighbour_coords] = (Dictionary.possible_letters(post_pattern), middle_points + end_points)

    def update_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Direction.LEFT, self.neighbours[Direction.DOWN])

    def update_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Direction.UP, self.neighbours[Direction.RIGHT])

    def update_neighbours(self):
        first_tile_coords = None
        for tile_coords in self.new_tiles:

            if tile_coords in self.neighbours[Direction.DOWN]:
                del self.neighbours[Direction.DOWN][tile_coords]

            if tile_coords in self.neighbours[Direction.RIGHT]:
                del self.neighbours[Direction.RIGHT][tile_coords]

            if not first_tile_coords:
                first_tile_coords = tile_coords
                self.update_horizontal_neighbours(tile_coords)
                self.update_vertical_neighbours(tile_coords)
            else:
                if first_tile_coords.is_same_column(tile_coords):
                    self.update_horizontal_neighbours(tile_coords)
                else:
                    self.update_vertical_neighbours(tile_coords)

    def add_neighbourhood(self, neighbourhood, direction, offset=0, max_opposite_length=3):
        self.neighbourhoods_to_check[direction][neighbourhood] = (offset, max_opposite_length)
        self.new_neighbourhoods_to_check[direction][neighbourhood] = (offset, max_opposite_length)

    def add_tile_neighbourhoods(self, tile, direction):
        neighbourhood = self.find_closest_neighbourhood(tile, direction)
        offset = 0 if direction.value > 0 else 1
        if neighbourhood:
            self.add_neighbourhood(neighbourhood, direction, offset)
            self.add_neighbourhood(neighbourhood, direction.perpendicular(), 1)
            self.add_neighbourhood(neighbourhood, direction.perpendicular().opposite(), 2)

    def prepare_neighbourhoods_to_check(self):
        for direction in Direction:
            self.new_neighbourhoods_to_check[direction].clear()

        if not self.new_tiles:
            if len(self.tiles_on_board) == 0:
                neighbourhood = Coords.central()
                self.add_neighbourhood(neighbourhood, Direction.LEFT, 1)
                self.add_neighbourhood(neighbourhood, Direction.RIGHT, 2)
            return

        first_tile = min(self.new_tiles)
        last_tile = max(self.new_tiles)

        direction = Direction.UP if Coords.is_same_column(first_tile, last_tile) else Direction.LEFT
        direct_coords, opposite_coords = Coords.get_functions(direction)

        while self.tiles_on_board.get(direct_coords(first_tile)):
            first_tile = direct_coords(first_tile)
        while self.tiles_on_board.get(opposite_coords(last_tile)):
            last_tile = opposite_coords(last_tile)

        for tile in self.new_tiles:
            self.add_tile_neighbourhoods(tile, direction.perpendicular())
            self.add_tile_neighbourhoods(tile, direction.perpendicular().opposite())

        self.add_tile_neighbourhoods(first_tile, direction)
        self.add_tile_neighbourhoods(last_tile, direction.opposite())

    def find_new_words(self, neighbourhoods_to_check, words, processes):
        for direction in Direction:
            process = Process(target=AI.find_new_word_with_direction,
                              args=(self.tiles_on_board, self.rack, direction, neighbourhoods_to_check[direction],
                                    self.neighbours[direction], words))
            processes.append(process)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def closest_word_bonus(self, tile_coords, direction):
        coords = tile_coords.on_direction(direction)
        distance = 1
        tiles_behind = ''

        while coords.is_valid() and distance <= 7:
            if self.tiles_on_board.get(coords) or self.tiles_on_board.get(
                    coords.on_direction(direction.perpendicular())) or self.tiles_on_board.get(
                    coords.on_direction(direction.perpendicular().opposite())):
                return
            if coords in double_word_bonus_coords:
                bonus = 2
                break
            elif coords in triple_word_bonus_coords:
                bonus = 3
                break
            coords.go(direction)
            distance += 1
        else:
            return

        coords.go(direction)
        while tile := self.tiles_on_board.get(coords):
            letter, _ = tile
            tiles_behind += letter
            coords.go(direction)

        return distance, bonus, tiles_behind

    def count_letters(self, letters_to_count):
        count = 0
        for letter in letters_to_count:
            count += self.letters_remaining.count(letter.upper())

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

        # How many points are letters the word worth
        points_for_letters = 0
        # How many blanks does the word contain
        blanks_in_word = 0
        # What is the direction of the word

        blanks_remaining = self.letters_remaining.count(BLANK)

        first_coords = min(word.positions)
        last_coords = max(word.positions)

        # neighbourhood_of_first = first_coords.on_direction.word.direction.perpendicular()
        # if not tiles.get(neighbourhood_of_first):
        #
        #     for coords in neighbours:
        #         pass
        #     bonus = AI.closest_word_bonus()
        # first_coords.on_direction.word.direction.perpendicular().opposite()
        # bonus = AI.closest_word_bonus(first_coords.on_direction.word.direction.perpendicular(),
        #                               word.direction.opposite(), tiles)

        for coords in word.added_letters:
            letter, points = word.added_letters.get(coords)
            points_for_letters += points
            if points == 0:
                blanks_in_word += 1

        # bonus = AI.closest_word_bonus(coords, word.direction, tiles)

        letters_factor = word_points
        if blanks_in_word and len(self.letters_remaining) - len(word.word) > MAX_RACK_SIZE:
            letters_factor -= 40

        if letters_factor < 0:
            return

        letters_factor /= points_for_letters * 2
        if letters_factor > 1:
            letters_factor = 1

        possible_letters = list(set(word.possible_prefix()) | set(word.possible_suffix()))
        expandability = self.calculate_expandability(possible_letters)

        evaluation_points = word_points * letters_factor * (1 - expandability / 2)

        print(word, word_points, letters_factor, expandability, evaluation_points)

        return evaluation_points

    def choose_word(self):
        self.word = self.words_by_points.get(max(self.words_by_points))[0]

    def add_valid_words(self, words):
        coords_to_check = set(self.new_tiles)
        for direction in Direction:
            coords_to_check.update(list(self.new_neighbourhoods_to_check[direction]))
        while words:
            word = words.pop()
            if coords_to_check.isdisjoint(word.positions):
                self.evaluate_word(word)
                AI.add_word(self.words_by_points, word, self.evaluate_word)

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
        self.update_neighbours()
        # I remove coords of tiles of the word I placed
        self.remove_latest_from_neighbourhoods()
        # I search for neighbours around placed word
        self.prepare_neighbourhoods_to_check()
        # I look for words
        self.find_new_words(self.neighbourhoods_to_check, self.no_turn_words, self.no_turn_processes)
        # I allow myself to start turn

    # I start turn after finishing no_turn if player has placed his word
    def turn(self):
        # I wait for player to finish
        while not self.is_turn:
            sleep(0.1)

        self.add_new_tiles()

        self.remove_latest_from_neighbourhoods()

        self.update_neighbours()

        self.prepare_neighbourhoods_to_check()

        self.find_new_words(self.new_neighbourhoods_to_check, self.turn_words, self.turn_processes)

    def run(self):
        while True:
            self.turn()
            self.end_turn()
            self.no_turn()

    def end_turn(self):
        wait_for_processes(self.no_turn_processes)

        self.add_valid_words(self.no_turn_words)

        wait_for_processes(self.turn_processes)

        while self.turn_words:
            word = self.turn_words.pop()
            self.evaluate_word(word)
            AI.add_word(self.words_by_points, word, self.evaluate_word)

        # I forget last word
        self.word = None

        self.choose_word()

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
