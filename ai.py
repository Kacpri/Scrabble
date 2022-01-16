from board_utils import *
from dictionary import BLANK, possible_letters
from word import Word
from enum import Enum
from time import sleep
from multiprocessing import Manager, Process


class Directions(Enum):
    up = 1
    down = -1
    left = 2
    right = -2


def opposite(direction):
    return Directions(-direction.value)


def perpendicular(direction):
    if abs(direction.value) == Directions.up.value:
        return Directions.left
    return Directions.up


def get_functions(direction):
    if direction == Directions.up:
        return Coords.above, Coords.below
    elif direction == Directions.down:
        return Coords.below, Coords.above
    elif direction == Directions.left:
        return Coords.on_left, Coords.on_right
    elif direction == Directions.right:
        return Coords.on_right, Coords.on_left
    else:
        return None


def add_word(words_dict, word):
    if word.is_in_dictionary():
        words_dict.append(word)
        # points = word.sum_up()
        # if not words_dict.get(points):
        #     words_dict[points] = []
        # words_dict.get(points).append(word)


def check_neighbourhood(tiles_list, coords, words, direction):
    while True:
        coords = direction(coords)
        neighbourhood = tiles_list.get(coords)
        if not neighbourhood:
            return coords
        is_blank = neighbourhood[1] == 0
        for word in words:
            word.add_letter(neighbourhood[0], coords, 0, False, is_blank)


def find_new_word_with_direction(tiles_on_board, rack, direction, neighbourhoods_to_check, neighbours, words):
    direct_coords, opposite_coords = get_functions(direction)
    for current in neighbourhoods_to_check:
        offset, max_opposite_length = neighbourhoods_to_check.get(current)
        all_words = [[] for _ in range(9)]
        first_word = Word(rack, neighbours)
        first_neighbour_coords = check_neighbourhood(tiles_on_board, current, [first_word], opposite_coords)
        all_words[0] = [first_word]
        for direct_level in range(1, len(rack)):
            all_words[direct_level] = []
            for word in all_words[direct_level - 1]:
                all_words[direct_level].extend(word.generate_children(current))

            if not all_words[direct_level]:
                break

            next_neighbour_coords = first_neighbour_coords
            previous_neighbour_coords = direct_coords(current)
            if previous_neighbour_coords.is_valid() and tiles_on_board.get(previous_neighbour_coords):
                previous_neighbour_coords = check_neighbourhood(tiles_on_board, current, all_words[direct_level],
                                                                direct_coords)
            for word in all_words[direct_level]:
                add_word(words, word)

            stop_value = direct_level - offset
            if direct_level > len(rack) / 2:
                stop_value = len(rack) - direct_level
            for opposite_level in range(stop_value):
                if not next_neighbour_coords.is_valid():
                    break
                current = next_neighbour_coords
                level = direct_level + opposite_level + 1
                all_words[level] = []

                for word in all_words[level - 1]:
                    all_words[level].extend(word.generate_children(current))

                next_neighbour_coords = opposite_coords(current)

                if tiles_on_board.get(next_neighbour_coords):
                    next_neighbour_coords = check_neighbourhood(tiles_on_board, current, all_words[level],
                                                                opposite_coords)

                for word in all_words[level]:
                    add_word(words, word)

            if not previous_neighbour_coords.is_valid():
                break
            current = previous_neighbour_coords


class AI:
    def __init__(self, tiles, sack):
        self.tiles = tiles
        self.tiles_on_board = {}
        self.new_tiles = None
        self.sack = sack

        self.word = None
        self.manager = Manager()
        self.words = self.manager.list()
        self.rack = self.sack.draw()
        horizontal = {}
        vertical = {}
        self.neighbours = {Directions.up: vertical, Directions.down: vertical,
                           Directions.left: horizontal, Directions.right: horizontal}
        self.blanks = []
        self.neighbourhoods_to_check = {}
        self.new_neighbourhoods_to_check = {}
        for direction in Directions:
            self.neighbourhoods_to_check[direction] = {}
            self.new_neighbourhoods_to_check[direction] = {}

        self.is_turn = True
        self.is_no_turn = False

    def find_new_tiles(self):
        self.new_tiles = []
        for tile_coords in self.tiles:
            if tile_coords.is_valid() and tile_coords not in self.tiles_on_board:
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
        direct_coords, _ = get_functions(direction)
        neighbour = direct_coords(tile_coords)
        while self.tiles_on_board.get(neighbour):
            neighbour = direct_coords(neighbour)

        if neighbour.is_valid():
            return neighbour
        return None

    def find_neighbours(self, tile_coords, direction, neighbours):
        direct_coords, opposite_coords = get_functions(direction)

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

            if self.tiles_on_board.get(tile_coords)[1] == 0:
                self.blanks.append(tile_coords)

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
            self.add_neighbourhood(neighbourhood, perpendicular(direction), 1)
            self.add_neighbourhood(neighbourhood, opposite(perpendicular(direction)), 2)

    def prepare_neighbourhoods_to_check(self):
        if not self.new_tiles:
            if len(self.tiles_on_board) == 0:
                neighbourhood = Coords.central()
                self.add_neighbourhood(neighbourhood, Directions.left, 1)
                self.add_neighbourhood(neighbourhood, Directions.right, 2)
            return

        for direction in Directions:
            self.new_neighbourhoods_to_check[direction].clear()

        first_tile = self.new_tiles[0]
        last_tile = self.new_tiles[-1]

        direction = Directions.up if Coords.is_same_column(first_tile, last_tile) else Directions.left
        direct_coords, opposite_coords = get_functions(direction)

        while self.tiles_on_board.get(direct_coords(first_tile)):
            first_tile = direct_coords(first_tile)
        while self.tiles_on_board.get(opposite_coords(last_tile)):
            last_tile = opposite_coords(last_tile)

        for tile in self.new_tiles:
            self.add_tile_neighbourhoods(tile, perpendicular(direction))
            self.add_tile_neighbourhoods(tile, opposite(perpendicular(direction)))

        self.add_tile_neighbourhoods(first_tile, direction)
        self.add_tile_neighbourhoods(last_tile, opposite(direction))

    # def check_neighbourhood(self, coords, words, direction):
    #     while True:
    #         coords = direction(coords)
    #         neighbourhood = self.tiles_on_board.get(coords)
    #         if not neighbourhood:
    #             return coords
    #         is_blank = neighbourhood[1] == 0
    #         for word in words:
    #             word.add_letter(neighbourhood[0], coords, 0, False, is_blank)

    # def add_word(self, word):
    #     if word.is_in_dictionary():
    #         points = word.sum_up()
    #         if not self.words_by_points.get(points):
    #             self.words_by_points[points] = []
    #         self.words_by_points.get(points).append(word)

    # def find_new_word_with_direction(self, direction, neighbourhoods_to_check):
    #     neighbours = self.neighbours[direction]
    #     direct_coords, opposite_coords = get_functions(direction)
    #     for current in neighbourhoods_to_check:
    #         offset, max_opposite_length = neighbourhoods_to_check.get(current)
    #         all_words = [[] for _ in range(9)]
    #         first_word = Word(self.rack, neighbours)
    #         first_neighbour_coords = self.check_neighbourhood(current, [first_word], opposite_coords)
    #         all_words[0] = [first_word]
    #         for direct_level in range(1, len(self.rack)):
    #             all_words[direct_level] = []
    #             for word in all_words[direct_level - 1]:
    #                 all_words[direct_level].extend(word.generate_children(current))
    #
    #             if not all_words[direct_level]:
    #                 break
    #
    #             next_neighbour_coords = first_neighbour_coords
    #             previous_neighbour_coords = direct_coords(current)
    #             if previous_neighbour_coords.is_valid() and self.tiles_on_board.get(previous_neighbour_coords):
    #                 previous_neighbour_coords = self.check_neighbourhood(current, all_words[direct_level],
    #                                                                      direct_coords)
    #             for word in all_words[direct_level]:
    #                 self.add_word(word)
    #
    #             stop_value = direct_level - offset
    #             if direct_level > len(self.rack) / 2:
    #                 stop_value = len(self.rack) - direct_level
    #             for opposite_level in range(stop_value):
    #                 if not next_neighbour_coords.is_valid():
    #                     break
    #                 current = next_neighbour_coords
    #                 level = direct_level + opposite_level + 1
    #                 all_words[level] = []
    #
    #                 for word in all_words[level - 1]:
    #                     all_words[level].extend(word.generate_children(current))
    #
    #                 next_neighbour_coords = opposite_coords(current)
    #
    #                 if self.tiles_on_board.get(next_neighbour_coords):
    #                     next_neighbour_coords = self.check_neighbourhood(current, all_words[level], opposite_coords)
    #
    #                 for word in all_words[level]:
    #                     self.add_word(word)
    #
    #             if not previous_neighbour_coords.is_valid():
    #                 break
    #             current = previous_neighbour_coords

    def find_new_words(self, neighbourhoods_to_check):
        processes = []
        for direction in Directions:
            process = Process(target=find_new_word_with_direction,
                              args=(self.tiles_on_board, self.rack, direction, neighbourhoods_to_check[direction],
                                    self.neighbours[direction], self.words))
            processes.append(process)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def choose_word(self):
        self.word = Word([], None)
        for word in self.words:
            if word.points > self.word.points:
                self.word = word

    def remove_invalid_words(self):
        coords_to_check = set(self.new_tiles)
        for direction in Directions:
            coords_to_check.update(list(self.new_neighbourhoods_to_check[direction]))

        for points in self.words:
            for word in self.words[points]:
                if not coords_to_check.isdisjoint(word.positions):
                    self.words[points].remove(word)

    def place_word(self):
        for letter, points, coords in self.word.added_letters:
            self.rack.remove(letter if points else BLANK)
            self.tiles_on_board[coords] = (letter, points)

    # I start no_turn after my move when player is thinking
    def no_turn(self):
        sleep(0.1)
        self.is_no_turn = True
        # and every word I found
        self.words[:] = []
        # I search for neighbours around placed word
        self.find_new_neighbours()
        # I remove coords of tiles of the word I placed
        self.remove_latest_from_neighbourhoods()
        # I search for neighbours around placed word
        self.prepare_neighbourhoods_to_check()
        # I look for words
        self.find_new_words(self.neighbourhoods_to_check)
        # I allow myself to start turn

        self.is_no_turn = False

    # I start turn after finishing no_turn if player has placed his word
    def turn(self):
        print(self.rack)
        self.is_turn = True
        # I wait for no_turn to finish
        while self.is_no_turn:
            sleep(0.2)
        # I forget last word
        self.word = None

        self.find_new_tiles()

        self.remove_latest_from_neighbourhoods()

        self.find_new_neighbours()

        self.prepare_neighbourhoods_to_check()

        self.remove_invalid_words()
        self.find_new_words(self.new_neighbourhoods_to_check)
        self.choose_word()

        self.end_turn()

        self.is_turn = False
        self.no_turn()

    def end_turn(self):
        if not self.word:
            # exchange letters here or wait
            return
        self.place_word()
        self.rack.extend(self.sack.draw(7 - len(self.rack)))
