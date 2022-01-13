import threading

from PyQt5.QtCore import QPointF

from board_utils import *
from dictionary import *
from word import Word
from tile import Tile
from enum import Enum


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


class AI:
    def __init__(self, scene, tiles, sack):
        self.scene = scene
        self.tiles = tiles
        self.tiles_on_board = {}
        self.new_tiles = None
        self.sack = sack

        self.word = None
        self.words_by_points = {}
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

    # def find_all_permutations(self):
    #     all_permutations = []
    #     for length in range(1, 8):
    #         all_permutations = all_permutations + list(permutations(self.rack, length))
    #
    #     self.all_permutations.clear()
    #     for permutation in all_permutations:
    #         self.all_permutations.append("".join(permutation))
    #     for permutation in self.all_permutations:
    #         if '_' in permutation:
    #             for letter in Sack.values_without_blank():
    #                 self.all_permutations = self.all_permutations + permutation.replace('_', letter)
    #             self.all_permutations.remove(permutation)

    def find_new_tiles(self):
        self.new_tiles = []
        for tile_coords in self.tiles:
            if tile_coords.is_valid() and tile_coords not in self.tiles_on_board:
                self.new_tiles.append(tile_coords)
                self.tiles_on_board[tile_coords] = self.tiles.get(tile_coords)

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
            sequence = neighbour.letter + sequence if reversed_order else sequence + neighbour.letter
            points += neighbour.points
            neighbour_coords = neighbour.coords
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

        tile = self.tiles_on_board.get(tile_coords)
        start = ""
        middle = tile.letter
        middle_points = tile.points
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

            if self.tiles_on_board.get(tile_coords).points == 0:
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

        print('vertical')
        for neighbour in self.neighbours[Directions.down]:
            print(f'{neighbour}: {self.neighbours[Directions.down].get(neighbour)}')
        print('horizontal')
        for neighbour in self.neighbours[Directions.right]:
            print(f'{neighbour}: {self.neighbours[Directions.right].get(neighbour)}')
        print('-----------------------------------------------------------------------------')

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

        first_tile = self.new_tiles[0]
        last_tile = self.new_tiles[-1]

        if first_tile.is_same_column(last_tile):
            direction = Directions.up
            while self.tiles_on_board.get(first_tile.above()):
                first_tile = first_tile.above()
            while self.tiles_on_board.get(last_tile.below()):
                last_tile = last_tile.below()

        else:
            direction = Directions.left
            while self.tiles_on_board.get(first_tile.on_left()):
                first_tile = first_tile.on_left()
            while self.tiles_on_board.get(last_tile.on_right()):
                last_tile = last_tile.on_right()

        for tile in self.new_tiles:
            self.add_tile_neighbourhoods(tile, perpendicular(direction))
            self.add_tile_neighbourhoods(tile, opposite(perpendicular(direction)))

        self.add_tile_neighbourhoods(first_tile, direction)
        self.add_tile_neighbourhoods(last_tile, opposite(direction))

    # def check_neighbourhood(self, coords, word, direction):
    #     while neighbour := self.get_tile(coords):
    #         is_blank = neighbour.points == 0
    #         word.add_letter(neighbour.letter, coords, False, is_blank)
    #         coords = direction(coords)
    #     return coords

    def check_neighbourhood(self, coords, words, direction):
        while True:
            coords = direction(coords)
            neighbourhood = self.tiles_on_board.get(coords)
            if not neighbourhood:
                return coords
            is_blank = neighbourhood.points == 0
            for word in words:
                word.add_letter(neighbourhood.letter, coords, 0, False, is_blank)

    def add_word(self, word):
        if word.is_in_dictionary():
            points = word.sum_up()
            if not self.words_by_points.get(points):
                self.words_by_points[points] = []
            self.words_by_points.get(points).append(word)

    def find_new_word_with_direction(self, direction, neighbourhoods_to_check):
        neighbours = self.neighbours[direction]
        direct_coords, opposite_coords = get_functions(direction)
        for current in neighbourhoods_to_check:
            offset, max_opposite_length = neighbourhoods_to_check.get(current)
            all_words = [[] for _ in range(9)]
            first_word = Word(self.rack, neighbours)
            first_neighbour_coords = self.check_neighbourhood(current, [first_word], opposite_coords)
            all_words[0] = [first_word]
            for direct_level in range(1, len(self.rack)):
                all_words[direct_level] = []
                for word in all_words[direct_level - 1]:
                    all_words[direct_level].extend(word.generate_children(current))

                if not all_words[direct_level]:
                    break

                next_neighbour_coords = first_neighbour_coords
                previous_neighbour_coords = direct_coords(current)
                if previous_neighbour_coords.is_valid() and self.tiles_on_board.get(previous_neighbour_coords):
                    previous_neighbour_coords = self.check_neighbourhood(current, all_words[direct_level],
                                                                         direct_coords)
                for word in all_words[direct_level]:
                    self.add_word(word)

                stop_value = direct_level - offset
                if direct_level > len(self.rack) / 2:
                    stop_value = len(self.rack) - direct_level
                for opposite_level in range(stop_value):
                    if not next_neighbour_coords.is_valid():
                        break
                    current = next_neighbour_coords
                    level = direct_level + opposite_level + 1
                    all_words[level] = []

                    for word in all_words[level - 1]:
                        all_words[level].extend(word.generate_children(current))

                    next_neighbour_coords = opposite_coords(current)

                    if self.tiles_on_board.get(next_neighbour_coords):
                        next_neighbour_coords = self.check_neighbourhood(current, all_words[level], opposite_coords)

                    for word in all_words[level]:
                        self.add_word(word)

                if not previous_neighbour_coords.is_valid():
                    break
                current = previous_neighbour_coords

    def find_new_words(self, neighbourhoods_to_check):
        for direction in Directions:
            self.find_new_word_with_direction(direction, neighbourhoods_to_check[direction])

    def choose_word(self):
        for points in sorted(self.words_by_points, reverse=True):
            word_list = self.words_by_points[points]
            self.word = word_list[0]
            return

    def place_word(self):
        added_tiles = {}
        for count in range(len(self.word.positions)):
            coords = self.word.positions[count]
            if self.tiles_on_board.get(coords):
                continue
            letter = self.word.word[count]
            if letter in self.rack:
                self.rack.remove(letter)
            else:
                self.rack.remove(BLANK)

            points = Sack.values.get(letter)
            if coords in self.word.blanks:
                points = 0

            position = QPointF(coords.x() * 40.0 + 30, coords.y() * 40.0 + 22)

            tile = Tile(letter, points, position)
            tile.set_immovable()
            self.tiles[coords] = tile
            self.tiles_on_board[coords] = tile
            added_tiles[coords] = tile
            self.scene.addItem(tile)
        self.new_tiles = sorted(added_tiles)

    def remove_invalid_words(self):
        coords_to_check = set(self.new_tiles)
        for direction in Directions:
            coords_to_check.update(list(self.new_neighbourhoods_to_check[direction]))

        for points in self.words_by_points:
            for word in self.words_by_points[points]:
                if not coords_to_check.isdisjoint(word.positions):
                    self.words_by_points[points].remove(word)

    # I start no_turn after my move when player is thinking
    def no_turn(self):
        # I forget placed word
        self.word = None
        # and every word I found
        self.words_by_points.clear()
        # I search for neighbours around placed word
        self.find_new_neighbours()
        # I remove coords of tiles of the word I placed
        self.remove_latest_from_neighbourhoods()
        # I search for neighbours around placed word
        self.prepare_neighbourhoods_to_check()
        # I look for words
        self.find_new_words(self.neighbourhoods_to_check)
        pass

    # I start turn after finishing no_turn if player has placed his word
    def turn(self):
        for direction in Directions:
            self.new_neighbourhoods_to_check[direction].clear()

        self.find_new_tiles()

        self.remove_latest_from_neighbourhoods()

        self.find_new_neighbours()

        self.prepare_neighbourhoods_to_check()

        self.remove_invalid_words()

        self.find_new_words(self.new_neighbourhoods_to_check)
        self.choose_word()
        if self.word:
            self.place_word()
            self.end_turn()
            return self.word.sum_up(), self.word.word

        return 0, None

    def end_turn(self):
        self.rack.extend(self.sack.draw(7 - len(self.rack)))
