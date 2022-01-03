from board_utils import *
from dictionary import *
from word import Word


class AI:
    def __init__(self, latest_tiles, tiles, sack):
        self.tiles = tiles
        self.latest_tiles = latest_tiles
        self.sack = sack

        self.words = None
        self.rack = ['W', 'Z', 'K', 'A', 'E', 'S', 'R']
        # self.rack = self.sack.draw(7)
        self.permutations = None
        self.vertical_neighbours = {}
        self.horizontal_neighbours = {}
        self.neighbours_to_check_upwards = None
        self.neighbours_to_check_downwards = None
        self.neighbours_to_check_leftwards = None
        self.neighbours_to_check_rightwards = None
        self.all_permutations = []

    def get_tile(self, coords):
        return self.tiles.get(coords)

    def is_opposite_vertical_neighbour(self, neighbour, another_neighbour):
        if neighbour.y() == another_neighbour.y():
            if neighbour.x() == another_neighbour.x():
                return False
            elif another_neighbour.x() < neighbour.x():
                neighbour, another_neighbour = another_neighbour, neighbour
            while neighbour := neighbour.on_right():
                if neighbour == another_neighbour:
                    return True
                if not self.get_tile(neighbour):
                    break
        return False

    def is_opposite_horizontal_neighbour(self, neighbour, another_neighbour):
        if neighbour.x() == another_neighbour.x():
            if neighbour.y() == another_neighbour.y():
                return False
            elif another_neighbour.y() < neighbour.y():
                neighbour, another_neighbour = another_neighbour, neighbour
            while neighbour := neighbour.below():
                if neighbour == another_neighbour:
                    return True
                if not self.get_tile(neighbour):
                    break

        return False

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
        while neighbour := self.get_tile(direction(neighbour_coords)):
            sequence = neighbour.letter + sequence if reversed_order else sequence + neighbour.letter
            neighbour_coords = neighbour.coords
        return sequence, neighbour_coords

    def find_neighbours(self, tile_coords, previous_coords, next_coords, neighbours):
        beginning = ""
        middle = self.latest_tiles[tile_coords].letter
        end = ""

        neighbour_coords = tile_coords
        middle, neighbour_coords = self.find_sequence(previous_coords, neighbour_coords, middle, True)

        previous_neighbour_coords = previous_coords(neighbour_coords)

        neighbour_coords = previous_coords(neighbour_coords)
        beginning, neighbour_coords = self.find_sequence(previous_coords, neighbour_coords, beginning, True)

        neighbour_coords = tile_coords
        middle, neighbour_coords = self.find_sequence(next_coords, neighbour_coords, middle)

        next_neighbour_coords = next_coords(neighbour_coords)

        neighbour_coords = next_coords(neighbour_coords)
        end, neighbour_coords = self.find_sequence(next_coords, neighbour_coords, end)

        pattern = beginning + "_" + middle
        pattern2 = middle + "_" + end

        neighbours[previous_neighbour_coords] = possible_letters(pattern)
        neighbours[next_neighbour_coords] = possible_letters(pattern2)

    def find_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Coords.on_left, Coords.on_right, self.vertical_neighbours)

    def find_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, Coords.above, Coords.below, self.horizontal_neighbours)

    def find_new_neighbours(self):
        first_tile_coords = None
        for tile_coords in self.latest_tiles:
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

    def prepare_neighbours_to_check(self):
        # TODO needs_improvement
        self.neighbours_to_check_upwards = list(self.horizontal_neighbours.keys()) \
                                           + list(self.vertical_neighbours.keys())
        self.neighbours_to_check_downwards = self.neighbours_to_check_upwards[:]
        self.neighbours_to_check_leftwards = self.neighbours_to_check_upwards[:]
        self.neighbours_to_check_rightwards = self.neighbours_to_check_upwards[:]

    # def check_neighbourhood(self, coords, word, direction):
    #     while neighbour := self.get_tile(coords):
    #         is_blank = neighbour.points == 0
    #         word.add_letter(neighbour.letter, coords, False, is_blank)
    #         coords = direction(coords)
    #     return coords

    def check_neighbourhood(self, coords, words, direction):
        while True:
            coords = direction(coords)
            neighbour = self.get_tile(coords)
            if not neighbour:
                return coords
            is_blank = neighbour.points == 0
            for word in words:
                word.add_letter(neighbour.letter, coords, False, is_blank)

    # def check_neighbourhood_above(self, coords, word):
    #     return self.check_neighbourhood(coords, word, coords_above)
    #
    # def check_neighbourhood_below(self, coords, word):
    #     return self.check_neighbourhood(coords, word, coords_below)

    #
    # def check_neighbourhood_on_right(self, coords, word):
    #     return self.check_neighbourhood(coords, word, coords_on_right)
    #
    # def check_neighbourhood_on_left(self, coords, word):
    #     return self.check_neighbourhood(coords, word, coords_on_left)

    def add_word(self, word):
        if word.is_in_dictionary:
            word.sum_up()
            print(word)
            self.words.get(word.points).append(word)

    def find_new_word_with_direction(self, neighbours_to_check):
        if neighbours_to_check == self.neighbours_to_check_upwards:
            previous_coords = Coords.above
            next_coords = Coords.below
            neighbours = self.vertical_neighbours
            offset = 0
        elif neighbours_to_check == self.neighbours_to_check_downwards:
            previous_coords = Coords.below
            next_coords = Coords.above
            neighbours = self.vertical_neighbours
            offset = 1
        elif neighbours_to_check == self.neighbours_to_check_leftwards:
            previous_coords = Coords.on_left
            next_coords = Coords.on_right
            neighbours = self.horizontal_neighbours
            offset = 0
        elif neighbours_to_check == self.neighbours_to_check_rightwards:
            previous_coords = Coords.on_right
            next_coords = Coords.on_left
            neighbours = self.horizontal_neighbours
            offset = 1
        else:
            return
        # todo delete it
        for current in neighbours_to_check:
            all_words = [[] for _ in range(9)]
            first_word = Word(self.rack, neighbours)
            first_neighbour_coords = self.check_neighbourhood(current, [first_word], next_coords)
            all_words[0] = [first_word]
            for direct_level in range(1, 8):
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
                    stop_value = len(self.rack) - direct_level - offset
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
        self.find_new_word_with_direction(self.neighbours_to_check_upwards)
        self.find_new_word_with_direction(self.neighbours_to_check_downwards)
        self.find_new_word_with_direction(self.neighbours_to_check_leftwards)
        self.find_new_word_with_direction(self.neighbours_to_check_rightwards)

    def turn(self):
        self.find_new_neighbours()
        self.prepare_neighbours_to_check()
        # self.find_all_permutations()
        self.find_new_words()
        print('')

    def no_turn(self):
        print("noting")
