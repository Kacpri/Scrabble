from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import sack
from sack import Sack
from tile import Tile
from board_utils import *
from dictionary import is_word_in_dictionary
from ai import AI


class Board(QGraphicsView):
    def __init__(self, score):
        QGraphicsView.__init__(self)

        self.ROWS = 15
        self.COLUMNS = 15
        self.SIZE = 4

        # self.deltaF = 1.0

        self.SCALE_MANUAL = 10
        self.SHIFT_FOCUS = QPointF(0, 0)

        self.squares = {}
        self.bonus_fields = []
        self._double_word_bonuses = []
        self._triple_word_bonuses = []
        self._double_letter_bonuses = []
        self._triple_letter_bonuses = []

        self._tiles_in_rack = {}
        self._rack = []
        self._total_points = 0
        self._points = 0
        self._words = []
        self._is_connected = False

        # parameters visible for AI
        # score represents total score of both players
        self.score = score
        # latest tiles represent tiles added in last turn
        self.latest_tiles = {}
        # tiles represent all tiles on board
        self.tiles = {}
        # sack represents sack
        self.sack = Sack()
        self.ai = AI(self.latest_tiles, self.tiles, self.sack)

        self.create_bonus_fields()
        self.scene = QGraphicsScene()
        self.build_board_scene()
        self.setScene(self.scene)

    # def wheelEvent(self, event):
    #     delta = event.angleDelta()
    #     self.deltaF = 1 + float(delta.y() / 1200)
    #     self.scale(self.deltaF, self.deltaF)

    def add_word_and_points(self, column, row, direction, first=None, last=None):
        word = ''
        word_points = 0
        word_multiplier = 1

        if direction == 'horizontal':
            if not first:
                first = column
            if not last:
                last = column

            while self.tiles.get(Coords(first - 1, row)):
                first -= 1
            while self.tiles.get(Coords(last + 1, row)):
                last += 1

        elif direction == 'vertical':
            if not first:
                first = row
            if not last:
                last = row

            while self.tiles.get(Coords(column, first - 1)):
                first -= 1
            while self.tiles.get(Coords(column, last + 1)):
                last += 1

        if first == last:
            return

        for current in range(first, last + 1):
            coords = None
            if direction == 'horizontal':
                coords = Coords(current, row)
            elif direction == 'vertical':
                coords = Coords(column, current)

            tile = self.tiles.get(coords)
            if not tile:
                print("some mistake")
                return

            if not self.latest_tiles.get(coords):
                self._is_connected = True

            points = tile.points

            if self.latest_tiles.get(coords):
                if coords in self._double_letter_bonuses:
                    points *= 2
                elif coords in self._triple_letter_bonuses:
                    points *= 3
                elif coords in self._double_word_bonuses:
                    word_multiplier *= 2
                elif coords in self._triple_word_bonuses:
                    word_multiplier *= 3

            word_points += points
            word += tile.letter

        self._words.append(word)
        self._points += word_points * word_multiplier

    def end_turn(self):
        column = row = None
        columns = []
        rows = []
        self._is_connected = True

        if not self.tiles or not self.latest_tiles:
            print('Musisz najpierw wykonać ruch')
            return

        if not self.tiles.get(Coords(7, 7)):
            print('Pierwszy wyraz musi przechodzić przez środek')
            return

        if self.latest_tiles.get(Coords(7, 7)):
            self._is_connected = True

        for tile_coords in self.latest_tiles:
            tile = self.latest_tiles.get(tile_coords)
            if tile.letter == '_':
                new_letter = input("Jaką literą ma być blank?").upper()
                if new_letter in sack.Sack.values:
                    tile.change_blank(new_letter)
            x, y = tile_coords.get()
            if not column and not row:
                column, row = x, y
            elif column and row:
                if row == y:
                    column = rows = None
                elif column == x:
                    row = columns = None
                else:
                    print('Wyrazy muszą być ułożone w jednej linii')
                    return
            if column:
                if column == x:
                    rows.append(y)
                else:
                    print('Wyrazy muszą być ułożone w jednej linii')
                    return
            if row:
                if row == y:
                    columns.append(x)
                else:
                    print('Wyrazy muszą być ułożone w jednej linii')
                    return

        self._words = []
        self._points = 0

        if rows:
            self.add_word_and_points(column, rows[0], 'vertical', min(rows), max(rows))

            for row in rows:
                self.add_word_and_points(column, row, 'horizontal')

        elif columns:
            self.add_word_and_points(columns[0], row, 'horizontal', min(columns), max(columns))

            for column in columns:
                self.add_word_and_points(column, row, 'vertical')

        if not self._is_connected:
            print('Wyraz musi się stykać z występującymi już na planszy')
            return

        for word in self._words:
            if not is_word_in_dictionary(word):
                print(f'słowo {word} nie występuje w słowniku')
                return

        for tile_coords in self.latest_tiles.values():
            tile_coords.set_immovable()

        print(self._words)
        print(self._points)

        self.score.add_points('Gracz', self._points)
        self.add_letters_to_rack()
        self.ai.turn()
        self.latest_tiles.clear()

    def on_tile_move(self, tile):
        x, y = tile.coords.get()

        if y == 15 or y == 16 and not 3 < x < 12:
            tile.undo_move()
            return
        elif other_tile := self.latest_tiles.get(tile.coords):
            tile.swap_with_other(other_tile)

            self.tiles[tile.coords] = tile
            self.tiles[other_tile.coords] = other_tile

            if tile.coords.is_in_rack():
                self._tiles_in_rack[tile.coords] = tile
            else:
                self.latest_tiles[tile.coords] = tile

            if other_tile.coords.is_in_rack():
                self._tiles_in_rack[other_tile.coords] = other_tile
            else:
                self.latest_tiles[other_tile.coords] = other_tile

        elif self.tiles.get(tile.coords):
            tile.undo_move()
            return
        else:
            if y != 16 and tile.old_coords.y() == '16':
                self._rack.remove(tile.letter)
            del self.tiles[tile.old_coords]
            self.tiles[tile.coords] = tile

            if tile.coords.is_in_rack():
                self._tiles_in_rack[tile.coords] = tile
            else:
                self.latest_tiles[tile.coords] = tile

            if tile.old_coords.is_in_rack():
                del self._tiles_in_rack[tile.old_coords]
            else:
                del self.latest_tiles[tile.old_coords]
        if y == 16 and 3 < x < 12:
            self._rack.append(tile.letter)

    def build_board_scene(self):
        self.build_squares()
        self.build_bonus_fields()
        self.build_rack()
        self.build_labels()

    def build_squares(self):

        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)

        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                square = self.add_square(row, column, pen, brush)

                self.squares[Coords(row + 1, column + 1)] = square

    def build_bonus_fields(self):
        for bonus_field in self.bonus_fields:
            brush = bonus_field["Brush"]
            pen = None
            bonus_fields = []

            for position in bonus_field["Positions"]:
                square = self.squares[position]
                bonus_fields.append(square)

            paint_graphic_items(bonus_fields, pen, brush)

    def build_rack(self):
        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        for column in range(4, 12):
            self.add_square(16, column, pen, brush)
        self.add_letters_to_rack()

    def add_letters_to_rack(self):
        for column in range(4, 12):
            coords = Coords(column, 16)
            if not self.tiles.get(coords) and len(self._tiles_in_rack) < 7:
                letter = self.sack.draw_one()
                self._rack.append(letter)

                position = QPointF(column * 40.0 + 30, 16 * 40.0 + 22)
                points = Sack.values.get(letter)
                tile = Tile(letter, points, position, self.on_tile_move)
                self.scene.addItem(tile)
                self._tiles_in_rack[coords] = tile
                self.tiles[coords] = tile

    def add_square(self, row, column, pen, brush):
        height = self.SIZE * self.SCALE_MANUAL
        width = self.SIZE * self.SCALE_MANUAL

        column_distance = column * width
        row_distance = row * height

        screen_offset = 2 * self.SCALE_MANUAL

        x = column_distance + screen_offset
        y = row_distance + screen_offset

        rectangle = QRectF(x, y, width, height)

        return self.scene.addRect(rectangle, pen, brush)

    def build_labels(self):
        for number in range(1, 16):
            letter_position = QPointF(number * 40.0 - 3.0, 0.0)
            number_position = QPointF(5.0, number * 40.0 - 6.0)
            letter_label = QGraphicsSimpleTextItem(chr(number + ord('A') - 1))
            number = str(number)
            if len(number) < 2:
                number = ' ' + number
            number_label = QGraphicsSimpleTextItem(number)
            letter_label.setPos(letter_position)
            number_label.setPos(number_position)
            self.scene.addItem(number_label)
            self.scene.addItem(letter_label)

    def create_bonus_fields(self):

        triple_word_brush = QBrush(QColor(255, 0, 0, 180))
        triple_word_bonuses = {
            "Name": "triple word",
            "Brush": triple_word_brush,
            "Positions": triple_word_bonus_coords
        }
        self._triple_word_bonuses = triple_word_bonus_coords
        self.bonus_fields.append(triple_word_bonuses)

        double_word_brush = QBrush(QColor(255, 0, 0, 100))

        double_word_bonuses = {
            "Name": "double word",
            "Brush": double_word_brush,
            "Positions": double_word_bonus_coords
        }
        self._double_word_bonuses = double_word_bonus_coords
        self.bonus_fields.append(double_word_bonuses)

        triple_letter_brush = QBrush(QColor(0, 0, 255, 180))

        triple_letter_bonuses = {
            "Name": "triple letter",
            "Brush": triple_letter_brush,
            "Positions": triple_letter_bonus_coords
        }
        self._triple_letter_bonuses = triple_letter_bonus_coords
        self.bonus_fields.append(triple_letter_bonuses)

        double_letter_brush = QBrush(QColor(0, 0, 255, 100))

        double_letter_bonuses = {
            "Name": "double letter",
            "Brush": double_letter_brush,
            "Positions": double_letter_bonus_coords
        }
        self._double_letter_bonuses = double_letter_bonus_coords
        self.bonus_fields.append(double_letter_bonuses)
