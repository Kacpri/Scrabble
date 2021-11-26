from board_utils import *
from dictionary import *


class AI:
    def __init__(self, latest_tiles, tiles, sack):
        self.tiles = tiles
        self.latest_tiles = latest_tiles
        self.sack = sack

        self.words = {}
        self.rack = self.sack.draw(7)
        self.permutations = None
        self.vertical_neighbours = {}
        self.horizontal_neighbours = {}

    def get_tile(self, coords):
        return self.tiles.get(coords)

    def find_sequence(self, direction, first_neighbour_coords, sequence="", reversed_order=False):
        neighbour_coords = first_neighbour_coords
        while neighbour := self.get_tile(direction):
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

        print("")

    def find_vertical_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, coords_on_left, coords_on_right, self.vertical_neighbours)

    def find_horizontal_neighbours(self, tile_coords):
        self.find_neighbours(tile_coords, coords_above, coords_below, self.horizontal_neighbours)

    def turn(self):
        for tile_coords in self.latest_tiles:
            self.find_vertical_neighbours(tile_coords)
            self.find_horizontal_neighbours(tile_coords)

        print(self.horizontal_neighbours)
        print(self.vertical_neighbours)

    def no_turn(self):
        print("noting")
