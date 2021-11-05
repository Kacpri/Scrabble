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

    def turn(self):
        self.words = [set() for _ in range(16)]
        # words = self.board.dic

        for tile_coords in self.latest_tiles:
            self.vertical_neighbours[tile_coords] = None
            self.horizontal_neighbours[tile_coords] = None

            beginning = ""
            middle = self.latest_tiles[tile_coords].letter
            end = ""
            neighbour_coords = tile_coords
            while neighbour := tile_above(neighbour_coords, self.tiles):
                middle = neighbour.letter + middle
                neighbour_coords = neighbour.coords

            neighbour_coords = coords_above(neighbour_coords)
            while neighbour := tile_above(neighbour_coords, self.tiles):
                beginning = neighbour.letter + beginning
                neighbour_coords = neighbour.coords

            neighbour_coords = tile_coords
            while neighbour := tile_below(neighbour_coords, self.tiles):
                middle = middle + neighbour.letter
                neighbour_coords = neighbour.coords

            neighbour_coords = coords_below(neighbour_coords)
            while neighbour := tile_below(neighbour_coords, self.tiles):
                end = end + neighbour.letter
                neighbour_coords = neighbour.coords

            pattern = beginning + "_" + middle
            words = possible_words_with_blank(pattern)
            horizontal_neighbour = []
            for word in words:
                horizontal_neighbour.append(word[len(beginning):len(beginning) + 1])
            self.horizontal_neighbours[neighbour_coords] = horizontal_neighbour

            pattern = beginning + "_" + middle
            words = possible_words_with_blank(pattern)
            horizontal_neighbour = []
            for word in words:
                horizontal_neighbour.append(word[len(beginning):len(beginning) + 1])
            self.horizontal_neighbours[neighbour_coords] = horizontal_neighbour
            if not tile_above(tile_coords, self.tiles):
                neighbour_coords = coords_above(tile_coords)
                beginning = ""
                tile = self.latest_tiles.get(tile_coords)
                middle = tile.letter
                while neighbour := tile_above(neighbour_coords, self.tiles):
                    beginning += neighbour.letter
                    neighbour_coords = neighbour.coords
                beginning = beginning[::-1]
                neighbour = tile_below(tile_coords, self.tiles)
                while neighbour:
                    middle += neighbour.letter
                    neighbour = tile_below(neighbour.coords, self.tiles)

                print(words)

            elif not tile_below(tile_coords, self.tiles):
                print()
            if not tile_on_right(tile_coords, self.tiles):
                neighbour_coords = coords_on_right(tile_coords)
                beginning = ""
                tile = self.latest_tiles.get(tile_coords)
                middle = tile.letter
                while neighbour := tile_on_left(neighbour_coords, self.tiles):
                    beginning += neighbour.letter
                    neighbour_coords = neighbour.coords
                beginning = beginning[::-1]
                neighbour = tile_on_left(tile_coords, self.tiles)
                while neighbour:
                    middle += neighbour.letter
                    neighbour = tile_on_left(neighbour.coords, self.tiles)
                pattern = beginning + "_" + middle
                words = possible_words_with_blank(pattern)
                vertical_neighbour = []
                for word in words:
                    vertical_neighbour.append(word[len(beginning):len(beginning) + 1])
                self.vertical_neighbours[neighbour_coords] = vertical_neighbour
                print(words)
            elif not tile_on_left(tile_coords, self.tiles):
                print()

        print(self.horizontal_neighbours)
        print(self.vertical_neighbours)
        # for tile_coords in self.tiles.keys():
        #     coords = tile_coords.coords
        #     if is_coords_of_rack(coords):
        #         continue
        #     if not tile_above(coords, self.tiles):
        #         continue
        #     if not tile_on_right(coords, self.tiles):
        #         continue

    def no_turn(self):
        print("noting")
