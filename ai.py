from board_utils import *
from dictionary import BLANK, possible_letters
from word import Word
from enum import Enum
from time import sleep
from PyQt5.QtCore import QThread
from multiprocessing import Manager, Process


class Directions(Enum):
    up = 1
    down = -1
    left = 2
    right = -2

    def opposite(self):
        return Directions(-self.value)

    def perpendicular(self):
        return Directions(abs(self.value % 2) + 1)

    def get_functions(self):
        if self == Directions.up:
            return Coords.above, Coords.below
        elif self == Directions.down:
            return Coords.below, Coords.above
        elif self == Directions.left:
            return Coords.on_left, Coords.on_right
        elif self == Directions.right:
            return Coords.on_right, Coords.on_left


class AI(QThread):
    @classmethod
    def add_word(cls, words_dict, word):
        if word.is_in_dictionary():
            points = word.sum_up()
            if not words_dict.get(points):
                words_dict[points] = []
            words_dict.get(points).append(word)

    @classmethod
    def check_neighbourhood(cls, tiles_list, coords, words, direction):
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
        direct_coords, opposite_coords = direction.get_functions()
        for current in neighbourhoods_to_check:
            offset, max_opposite_length = neighbourhoods_to_check.get(current)
            all_words = [[] for _ in range(9)]
            first_word = Word(rack, neighbours)
            first_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, [first_word], opposite_coords)
            all_words[0] = [first_word]
            for direct_level in range(1, len(rack)):
                all_words[direct_level] = []
                for word in all_words[direct_level - 1]:
                    all_words[direct_level].extend(word.generate_children(current))

                if not all_words[direct_level]:
                    break

                next_neighbour_coords = first_neighbour_coords
                previous_neighbour_coords = direct_coords(current)
                if previous_neighbour_coords.is_on_board() and tiles_on_board.get(previous_neighbour_coords):
                    previous_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current,
                                                                        all_words[direct_level], direct_coords)
                for word in all_words[direct_level]:
                    cls.add_word(words_by_points, word)

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

                    next_neighbour_coords = opposite_coords(current)

                    if tiles_on_board.get(next_neighbour_coords):
                        next_neighbour_coords = cls.check_neighbourhood(tiles_on_board, current, all_words[level],
                                                                        opposite_coords)

                    for word in all_words[level]:
                        cls.add_word(words_by_points, word)

                if not previous_neighbour_coords.is_on_board():
                    break
                current = previous_neighbour_coords
        for points in sorted(words_by_points, reverse=True):
            count = 0
            for word in words_by_points.get(points):
                words.append(word)
                count += 1
                if count > 5:
                    break

    def __init__(self, tiles, sack):
        super().__init__()
        self.tiles = tiles
        self.sack = sack

        self.tiles_on_board = {}
        self.new_tiles = None

        self.word = None
        self.manager = Manager()
        self.words = self.manager.list()
        self.words_by_points = {}
        self.rack = self.sack.draw()

        horizontal = {}
        vertical = {}
        self.neighbours = {Directions.up: vertical, Directions.down: vertical,
                           Directions.left: horizontal, Directions.right: horizontal}

        self.neighbourhoods_to_check = {}
        self.new_neighbourhoods_to_check = {}
        for direction in Directions:
            self.neighbourhoods_to_check[direction] = {}
            self.new_neighbourhoods_to_check[direction] = {}

        self.is_turn = False

    def find_new_tiles(self):
        self.new_tiles = []
        for tile_coords in self.tiles:
            if tile_coords.is_on_board() and tile_coords not in self.tiles_on_board:
                self.new_tiles.append(tile_coords)
                self.tiles_on_board[tile_coords] = self.tiles.get(tile_coords).get_letter_and_points()

    def remove_neighbourhood_to_check(self, neighbour, direction):
        if self.neighbourhoods_to_check[direction].get(neighbour):
            del self.neighbourhoods_to_check[direction][neighbour]

    def remove_latest_from_neighbourhoods(self):
        for tile in self.new_tiles:
            for direction in Directions:
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
        direct_coords, _ = direction.get_functions()
        neighbour = direct_coords(tile_coords)
        while self.tiles_on_board.get(neighbour):
            neighbour = direct_coords(neighbour)

        if neighbour.is_on_board():
            return neighbour
        return None

    def find_neighbours(self, tile_coords, direction, neighbours):
        direct_coords, opposite_coords = direction.get_functions()

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

        neighbours[previous_neighbour_coords] = (possible_letters(pre_pattern), start_points + middle_points)
        neighbours[next_neighbour_coords] = (possible_letters(post_pattern), middle_points + end_points)

    def find_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Directions.left, self.neighbours[Directions.down])

    def find_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Directions.up, self.neighbours[Directions.right])

    def find_new_neighbours(self):
        first_tile_coords = None
        for tile_coords in self.new_tiles:

            if tile_coords in self.neighbours[Directions.down]:
                del self.neighbours[Directions.down][tile_coords]

            if tile_coords in self.neighbours[Directions.right]:
                del self.neighbours[Directions.right][tile_coords]

            if not first_tile_coords:
                first_tile_coords = tile_coords
                self.find_vertical_neighbours(tile_coords)
                self.find_horizontal_neighbours(tile_coords)
            else:
                if first_tile_coords.is_same_column(tile_coords):
                    self.find_vertical_neighbours(tile_coords)
                else:
                    self.find_horizontal_neighbours(tile_coords)

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
        for direction in Directions:
            self.new_neighbourhoods_to_check[direction].clear()

        if not self.new_tiles:
            if len(self.tiles_on_board) == 0:
                neighbourhood = Coords.central()
                self.add_neighbourhood(neighbourhood, Directions.left, 1)
                self.add_neighbourhood(neighbourhood, Directions.right, 2)
            return

        first_tile = self.new_tiles[0]
        last_tile = self.new_tiles[-1]

        direction = Directions.up if Coords.is_same_column(first_tile, last_tile) else Directions.left
        direct_coords, opposite_coords = direction.get_functions()

        while self.tiles_on_board.get(direct_coords(first_tile)):
            first_tile = direct_coords(first_tile)
        while self.tiles_on_board.get(opposite_coords(last_tile)):
            last_tile = opposite_coords(last_tile)

        for tile in self.new_tiles:
            self.add_tile_neighbourhoods(tile, direction.perpendicular())
            self.add_tile_neighbourhoods(tile, direction.perpendicular().opposite())

        self.add_tile_neighbourhoods(first_tile, direction)
        self.add_tile_neighbourhoods(last_tile, direction.opposite())

    def find_new_words(self, neighbourhoods_to_check):
        processes = []
        for direction in Directions:
            process = Process(target=AI.find_new_word_with_direction,
                              args=(self.tiles_on_board, self.rack, direction, neighbourhoods_to_check[direction],
                                    self.neighbours[direction], self.words))
            processes.append(process)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def choose_word(self):
        # self.word = Word([], None)
        # for word in self.words:
        #     if word.sum_up() > self.word.sum_up():
        #         self.word = word
        for points in sorted(self.words_by_points, reverse=True):
            self.word = self.words_by_points[points][0]
            break

    def remove_invalid_words(self):
        coords_to_check = set(self.new_tiles)
        for direction in Directions:
            coords_to_check.update(list(self.new_neighbourhoods_to_check[direction]))
        while self.words:
            word = self.words.pop()
            if coords_to_check.isdisjoint(word.positions):
                AI.add_word(self.words_by_points, word)

    def place_word(self):
        self.new_tiles = []
        for letter, points, coords in self.word.added_letters:
            self.rack.remove(letter if points else BLANK)
            self.tiles_on_board[coords] = (letter, points)
            self.new_tiles.append(coords)

    # I start no_turn after my move when player is thinking
    def no_turn(self):
        # and every word I found
        self.words[:] = []
        self.words_by_points.clear()
        # I search for neighbours around placed word
        self.find_new_neighbours()
        # I remove coords of tiles of the word I placed
        self.remove_latest_from_neighbourhoods()
        # I search for neighbours around placed word
        self.prepare_neighbourhoods_to_check()
        # I look for words
        self.find_new_words(self.neighbourhoods_to_check)
        # I allow myself to start turn

    # I start turn after finishing no_turn if player has placed his word
    def turn(self):
        # I wait for player to finish
        while not self.is_turn:
            sleep(0.1)
        # I forget last word
        self.word = None

        self.find_new_tiles()

        self.remove_latest_from_neighbourhoods()

        self.find_new_neighbours()

        self.prepare_neighbourhoods_to_check()

        self.remove_invalid_words()

        self.find_new_words(self.new_neighbourhoods_to_check)
        for word in self.words:
            AI.add_word(self.words_by_points, word)

        self.choose_word()

        self.end_turn()

        self.is_turn = False

    def run(self):
        while True:
            self.turn()
            self.finished.emit()
            self.no_turn()

    def end_turn(self):
        if not self.word:
            # exchange letters here or wait
            return
        self.place_word()
        self.rack.extend(self.sack.draw(7 - len(self.rack)))
