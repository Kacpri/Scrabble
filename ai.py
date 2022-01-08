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


class AI:
    def __init__(self, scene, latest_tiles, tiles, sack):
        self.scene = scene
        self.tiles = tiles
        self.sorted_latest_tiles = None
        self.latest_tiles = latest_tiles
        self.sack = sack

        self.word = None
        self.words = None
        self.rack = self.sack.draw(7)
        self.permutations = None
        self.vertical_neighbours = {}
        self.horizontal_neighbours = {}
        self.blanks = []
        self.neighbours_to_check = {}
        for direction in Directions:
            self.neighbours_to_check[direction] = {}
        self.all_permutations = []

    def get_bundle(self, direction):
        if direction == Directions.up:
            return Coords.above, Coords.below, self.vertical_neighbours, self.neighbours_to_check[Directions.up]
        elif direction == Directions.down:
            return Coords.above, Coords.below, self.vertical_neighbours, self.neighbours_to_check[Directions.down]
        elif direction == Directions.left:
            return Coords.on_left, Coords.on_right, self.horizontal_neighbours, self.neighbours_to_check[
                Directions.left]
        elif direction == Directions.right:
            return Coords.on_right, Coords.on_left, self.horizontal_neighbours, self.neighbours_to_check[
                Directions.right]
        else:
            return None

    # def is_opposite_vertical_neighbour(self, neighbour, another_neighbour):
    #     if neighbour.y() == another_neighbour.y():
    #         if neighbour.x() == another_neighbour.x():
    #             return False
    #         elif another_neighbour.x() < neighbour.x():
    #             neighbour, another_neighbour = another_neighbour, neighbour
    #         while neighbour := neighbour.on_right():
    #             if neighbour == another_neighbour:
    #                 return True
    #             if not self.get_tile(neighbour):
    #                 break
    #     return False
    #
    # def is_opposite_horizontal_neighbour(self, neighbour, another_neighbour):
    #     if neighbour.x() == another_neighbour.x():
    #         if neighbour.y() == another_neighbour.y():
    #             return False
    #         elif another_neighbour.y() < neighbour.y():
    #             neighbour, another_neighbour = another_neighbour, neighbour
    #         while neighbour := neighbour.below():
    #             if neighbour == another_neighbour:
    #                 return True
    #             if not self.get_tile(neighbour):
    #                 break
    #
    #     return False

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

    def find_sequence(self, direction, first_neighbour_coords, sequence="", reversed_order=False):
        neighbour_coords = first_neighbour_coords
        points = 0
        while neighbour := self.tiles.get(direction(neighbour_coords)):
            sequence = neighbour.letter + sequence if reversed_order else sequence + neighbour.letter
            points += neighbour.points
            neighbour_coords = neighbour.coords
        return sequence, neighbour_coords, points

    def find_neighbours(self, tile_coords, direction, neighbours):
        previous_coords, next_coords = self.get_bundle(direction)[:2]

        tile = self.tiles.get(tile_coords)
        start = ""
        middle = tile.letter
        middle_points = tile.points
        end = ""

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(previous_coords, neighbour_coords, middle, True)
        middle_points += points

        previous_neighbour_coords = previous_coords(neighbour_coords)

        neighbour_coords = previous_coords(neighbour_coords)
        start, neighbour_coords, start_points = self.find_sequence(previous_coords, neighbour_coords, start, True)

        neighbour_coords = tile_coords
        middle, neighbour_coords, points = self.find_sequence(next_coords, neighbour_coords, middle)
        middle_points += points

        next_neighbour_coords = next_coords(neighbour_coords)

        neighbour_coords = next_coords(neighbour_coords)
        end, neighbour_coords, end_points = self.find_sequence(next_coords, neighbour_coords, end)

        pre_pattern = start + BLANK + middle
        post_pattern = middle + BLANK + end

        neighbours[previous_neighbour_coords] = (possible_letters(pre_pattern), start_points + middle_points)
        neighbours[next_neighbour_coords] = (possible_letters(post_pattern), middle_points + end_points)

    def find_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Directions.left, self.vertical_neighbours)

    def find_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Directions.up, self.horizontal_neighbours)

    def find_new_neighbours(self):
        first_tile_coords = None
        for tile_coords in self.sorted_latest_tiles:

            if self.tiles.get(tile_coords).points == 0:
                self.blanks.append(tile_coords)

            if tile_coords in self.vertical_neighbours:
                del self.vertical_neighbours[tile_coords]

            if tile_coords in self.horizontal_neighbours:
                del self.horizontal_neighbours[tile_coords]

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
        for neighbour in self.horizontal_neighbours.keys():
            print(f'{neighbour}: {self.horizontal_neighbours.get(neighbour)}')
        print('horizontal')
        for neighbour in self.vertical_neighbours.keys():
            print(f'{neighbour}: {self.vertical_neighbours.get(neighbour)}')
        print('-----------------------------------------------------------------------------')

    def remove_neighbour(self, neighbour, direction):
        if self.neighbours_to_check[direction].get(neighbour):
            del self.neighbours_to_check[direction][neighbour]

    def remove_latest_from_neighbours(self):
        for tile in self.sorted_latest_tiles:
            for direction in Directions:
                self.remove_neighbour(tile, direction)

    def add_neighbour(self, neighbour, direction, offset=0, max_opposite_length=3):
        self.neighbours_to_check[direction][neighbour] = (offset, max_opposite_length)

    def prepare_neighbours_to_check(self):
        if not self.sorted_latest_tiles:
            if len(self.tiles) == 7:
                neighbour = Coords.central()
                for direction in Directions:
                    offset = 1 if direction.value > 0 else 2
                    self.add_neighbour(neighbour, direction, offset)
            return

        sorted_tiles = self.sorted_latest_tiles
        first_tile = sorted_tiles[0]
        last_tile = sorted_tiles[-1]

        if first_tile.is_same_column(last_tile):
            while self.tiles.get(first_tile.above()):
                first_tile = first_tile.above()
            while self.tiles.get(last_tile.below()):
                last_tile = last_tile.below()

            tile = first_tile
            while tile <= last_tile:
                neighbour = tile.on_left()
                if neighbour.is_valid() and not self.tiles.get(neighbour):
                    self.add_neighbour(neighbour, Directions.left)
                    self.add_neighbour(neighbour, Directions.up, 1)
                    self.add_neighbour(neighbour, Directions.down, 2)
                neighbour = tile.on_right()
                if neighbour.is_valid() and not self.tiles.get(neighbour):
                    self.add_neighbour(neighbour, Directions.right, 1)
                    self.add_neighbour(neighbour, Directions.up, 1)
                    self.add_neighbour(neighbour, Directions.down, 2)

                tile = tile.below()
            neighbour = first_tile.above()
            if neighbour.is_valid():
                self.add_neighbour(neighbour, Directions.up)
                self.add_neighbour(neighbour, Directions.left, 1)
                self.add_neighbour(neighbour, Directions.right, 2)
            neighbour = last_tile.below()
            if neighbour.is_valid():
                self.add_neighbour(neighbour, Directions.down, 1)
                self.add_neighbour(neighbour, Directions.left, 1)
                self.add_neighbour(neighbour, Directions.right, 2)

        else:
            while self.tiles.get(first_tile.on_left()):
                first_tile = first_tile.on_left()
            while self.tiles.get(last_tile.on_right()):
                last_tile = last_tile.on_right()

            tile = first_tile
            while tile <= last_tile:
                neighbour = tile.above()
                if neighbour.is_valid() and not self.tiles.get(neighbour):
                    self.add_neighbour(neighbour, Directions.up)
                    self.add_neighbour(neighbour, Directions.left, 1)
                    self.add_neighbour(neighbour, Directions.right, 2)

                neighbour = tile.below()
                if neighbour.is_valid() and not self.tiles.get(neighbour):
                    self.add_neighbour(neighbour, Directions.down, 1)
                    self.add_neighbour(neighbour, Directions.left, 1)
                    self.add_neighbour(neighbour, Directions.right, 2)

                tile = tile.on_right()

            neighbour = first_tile.on_left()
            if neighbour.is_valid():
                self.add_neighbour(neighbour, Directions.left)
                self.add_neighbour(neighbour, Directions.up, 1)
                self.add_neighbour(neighbour, Directions.down, 2)

            neighbour = last_tile.on_right()
            if neighbour.is_valid():
                self.add_neighbour(neighbour, Directions.right, 1)
                self.add_neighbour(neighbour, Directions.up, 1)
                self.add_neighbour(neighbour, Directions.down, 2)

    # def check_neighbourhood(self, coords, word, direction):
    #     while neighbour := self.get_tile(coords):
    #         is_blank = neighbour.points == 0
    #         word.add_letter(neighbour.letter, coords, False, is_blank)
    #         coords = direction(coords)
    #     return coords

    def check_neighbourhood(self, coords, words, direction):
        while True:
            coords = direction(coords)
            neighbour = self.tiles.get(coords)
            if not neighbour:
                return coords
            is_blank = neighbour.points == 0
            for word in words:
                word.add_letter(neighbour.letter, coords, False, is_blank)

    def add_word(self, word):
        if word.is_in_dictionary():
            print(word)
            self.words.get(word.sum_up()).append(word)

    def find_new_word_with_direction(self, direction):
        previous_coords, next_coords, neighbours, neighbours_to_check = self.get_bundle(direction)
        for current in neighbours_to_check:
            offset, max_opposite_length = neighbours_to_check.get(current)
            all_words = [[] for _ in range(9)]
            first_word = Word(self.rack, neighbours)
            first_neighbour_coords = self.check_neighbourhood(current, [first_word], next_coords)
            all_words[0] = [first_word]
            for direct_level in range(1, len(self.rack)):
                all_words[direct_level] = []
                for word in all_words[direct_level - 1]:
                    all_words[direct_level].extend(word.generate_children(current))

                if not all_words[direct_level]:
                    break

                next_neighbour_coords = first_neighbour_coords
                previous_neighbour_coords = previous_coords(current)
                if previous_neighbour_coords.is_valid() and self.tiles.get(previous_neighbour_coords):
                    previous_neighbour_coords = self.check_neighbourhood(current, all_words[direct_level],
                                                                         previous_coords)
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

                    next_neighbour_coords = next_coords(current)

                    if self.tiles.get(next_neighbour_coords):
                        next_neighbour_coords = self.check_neighbourhood(current, all_words[level], next_coords)

                    for word in all_words[level]:
                        self.add_word(word)

                if not previous_neighbour_coords.is_valid():
                    break
                current = previous_neighbour_coords

    def find_new_words(self):
        self.words = {}
        for count in range(200):
            self.words[count] = []
        for direction in Directions:
            self.find_new_word_with_direction(direction)

    def choose_word(self):
        for word_list in reversed(self.words.values()):
            if word_list:
                self.word = word_list[0]
                return

    def place_word(self):
        added_tiles = {}
        for count in range(len(self.word.positions)):
            coords = self.word.positions[count]
            if self.tiles.get(coords):
                continue
            letter = self.word.word[count]
            if letter in self.rack:
                self.rack.remove(letter)
            else:
                self.rack.remove()

            points = Sack.values.get(letter)
            if coords in self.word.blanks:
                points = 0

            position = QPointF(coords.x() * 40.0 + 30, coords.y() * 40.0 + 22)

            tile = Tile(letter, points, position)
            tile.set_immovable()
            self.tiles[coords] = tile
            added_tiles[coords] = tile
            self.scene.addItem(tile)
        self.sorted_latest_tiles = sorted(added_tiles)

    def end_turn(self):
        self.find_new_neighbours()
        self.remove_latest_from_neighbours()
        for direction in Directions:
            for neighbour in self.neighbours_to_check[direction]:
                if self.tiles.get(neighbour):
                    self.remove_latest_from_neighbours()
        self.prepare_neighbours_to_check()
        self.rack.extend(self.sack.draw(7 - len(self.rack)))

    def turn(self):
        self.word = None
        self.sorted_latest_tiles = sorted(self.latest_tiles)
        self.remove_latest_from_neighbours()
        self.find_new_neighbours()
        self.prepare_neighbours_to_check()
        for d in Directions:
            print(d)
            for n in self.neighbours_to_check[d]:
                print(n)

        self.find_new_words()
        self.choose_word()
        if self.word:
            self.place_word()
            self.end_turn()
            return self.word.sum_up()

        print('nie moge ulozyc')

        return 0

    def no_turn(self):
        print("noting")
