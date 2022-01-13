import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from dictionary import *
from sack import Sack
from tile import Tile
from board_utils import *
from ai import AI
import time
import random


class Board(QGraphicsView):
    def __init__(self, score, player_clock, ai_clock, set_comment, text_field, set_prompt, confirm_button):
        QGraphicsView.__init__(self)

        self.ROWS = 15
        self.COLUMNS = 15
        self.SIZE = 4

        self.SCALE_MANUAL = 10
        self.SHIFT_FOCUS = QPointF(0, 0)

        self.squares = {}
        self.bonus_fields = []
        self._double_word_bonuses = []
        self._triple_word_bonuses = []
        self._double_letter_bonuses = []
        self._triple_letter_bonuses = []

        self.create_bonus_fields()
        self.scene = QGraphicsScene()
        self.build_board_scene()
        load_data()
        self.setScene(self.scene)
        self.player_clock = player_clock
        self.ai_clock = ai_clock
        self.set_comment = set_comment
        self.set_prompt = set_prompt
        self.confirm_button = confirm_button
        self.text_field = text_field

        # parameters visible for AI
        # score represents total score of both players
        self.score = score
        # latest tiles represent tiles added in last turn
        self.latest_tiles = None
        # tiles represent all tiles on board
        self.tiles = None
        # sack represents sack
        self.sack = None
        self.tiles_in_rack = None
        self.tiles_to_exchange = None
        self._total_points = None
        self._points = None
        self._words = None
        self._is_connected = False
        self.is_ai_turn = None
        self.ai = None

    def prepare_game(self):
        self.sack = Sack()
        self.tiles = {}
        self.latest_tiles = {}
        self.tiles_in_rack = {}
        self.tiles_to_exchange = {}
        self.ai = AI(self.scene, self.tiles, self.sack)
        self._total_points = 0
        self._points = 0
        self._words = []
        self._is_connected = False

    def start_game(self):
        self.prepare_game()
        # self.is_ai_turn = bool(random.getrandbits(1))
        self.is_ai_turn = False
        self.add_letters_to_rack()
        self.player_clock.start()
        if self.is_ai_turn:
            self.set_comment('Przeciwnik myśli')
            # ai_thread = threading.Thread(target=self.ai.turn)
            # ai_thread.start()
            self.ai.turn()
            self.is_ai_turn = False
        return self.is_ai_turn

    def add_letters_to_rack(self, letters=None):
        if not letters:
            letters = self.sack.draw(7 - len(self.tiles_in_rack))
        index = 0
        for column in range(4, 12):
            coords = Coords(column, 16)
            if not self.tiles.get(coords) and len(self.tiles_in_rack) < 7:
                letter = letters[index]
                index += 1

                position = QPointF(column * 40.0 + 30, 16 * 40.0 + 22)
                points = Sack.values.get(letter)
                tile = Tile(letter, points, position, self.on_tile_move)
                self.scene.addItem(tile)
                self.tiles_in_rack[coords] = tile
                self.tiles[coords] = tile

    def exchange_letters(self):
        if self.is_ai_turn:
            self.set_comment('Ruch przeciwnika')
            return

        if not self.tiles_to_exchange:
            self.set_comment('Brak liter do wymiany')
            return

        letters_to_exchange = []
        for tile in self.tiles_to_exchange.values():
            letters_to_exchange.append(tile.letter)
            del self.tiles[tile.coords]
            self.scene.removeItem(tile)

        letters_on_board = []
        for tile in self.latest_tiles.values():
            letters_on_board.append(tile.letter)
            del self.tiles[tile.coords]
            self.scene.removeItem(tile)

        new_letters = self.sack.exchange(letters_to_exchange)
        self.tiles_to_exchange.clear()
        self.latest_tiles.clear()
        self.add_letters_to_rack(new_letters + letters_on_board)

        # self.ai.turn()

    def resign(self):
        for tile in self.tiles.values():
            self.scene.removeItem(tile)

        self.prepare_game()

    def end_turn(self):
        if self.is_ai_turn:
            self.set_comment('Ruch przeciwnika')
            return

        blank_tiles = []
        column = row = -1
        columns = []
        rows = []
        self._is_connected = True

        if not self.tiles or not self.latest_tiles:
            self.set_comment('Musisz najpierw wykonać ruch')
            return

        if not self.tiles.get(Coords.central()):
            self.set_comment('Pierwszy wyraz musi przechodzić przez środek')
            return

        if self.latest_tiles.get(Coords.central()):
            self._is_connected = True

        for tile_coords in self.latest_tiles:
            tile = self.latest_tiles.get(tile_coords)
            if tile.letter == BLANK:
                self.set_prompt("Jaką literą ma być blank?")
                self.text_field.setDisabled(False)
                self.text_field.returnPressed.connect(self.end_turn)
                self.confirm_button.setDisabled(False)
                if not self.text_field.text():
                    return

                new_letter = self.text_field.text()
                if new_letter.upper() in Sack.values:
                    tile.change_blank(new_letter.upper())
                    blank_tiles.append(tile)
                    self.text_field.setDisabled(True)
                    self.text_field.clear()
                    self.set_prompt('')
                    self.confirm_button.setDisabled(True)

                else:
                    self.set_comment('Podaj poprawną literę')
                    self.text_field.clear()
                    return

            x, y = tile_coords.get()
            if column < 0 and row < 0:
                column, row = x, y
            elif column and row:
                if row == y:
                    column = -1
                    rows = None
                elif column == x:
                    row = -1
                    columns = None
                else:
                    self.set_comment('Wyrazy muszą być ułożone w jednej linii')
                    return
            if column >= 0:
                if column == x:
                    rows.append(y)
                else:
                    self.set_comment('Wyrazy muszą być ułożone w jednej linii')
                    return
            if row >= 0:
                if row == y:
                    columns.append(x)
                else:
                    self.set_comment('Wyrazy muszą być ułożone w jednej linii')
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
            self.set_comment('Wyraz musi się stykać z występującymi już na planszy')
            return

        for word in self._words:
            if not is_word_in_dictionary(word):
                self.set_comment(f'słowo {word} nie występuje w słowniku')
                if blank_tiles:
                    for blank in blank_tiles:
                        blank.change_back()
                    self.end_turn()
                return

        for tile_coords in self.latest_tiles.values():
            tile_coords.set_immovable()

        print(self._words)
        print(self._points)

        self.score.add_points('Gracz', self._points)
        self.add_letters_to_rack()
        self.is_ai_turn = not self.is_ai_turn
        start = time.time()
        ai_points, ai_word = self.ai.turn()
        end = time.time()
        print(end - start)
        self.score.add_points('AI', ai_points)
        # ai_thread = threading.Thread(target=self.ai_turn)
        # ai_thread.start()
        print('ulozone')
        start = time.time()
        self.ai.no_turn()
        end = time.time()
        print(end - start)
        self.is_ai_turn = not self.is_ai_turn

        self.latest_tiles.clear()

    def ai_turn(self):
        self.ai.no_turn()
        while not self.is_ai_turn():
            self.sleep(0.1)
        ai_score, word = self.ai.turn()
        self.score.add_points('AI', ai_score)
        self.is_ai_turn = False

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

    def swap_tiles(self, tile, other_tile):
        tile.swap_with_other(other_tile)
        self.tiles[tile.coords] = tile
        self.tiles[other_tile.coords] = other_tile

        if tile.coords in self.latest_tiles:
            self.latest_tiles[tile.coords] = tile

        elif tile.coords in self.tiles_in_rack:
            self.tiles_in_rack[tile.coords] = tile

        elif tile.coords in self.tiles_to_exchange:
            self.tiles_to_exchange[tile.coords] = tile

        if other_tile.coords in self.latest_tiles:
            self.latest_tiles[other_tile.coords] = other_tile

        elif other_tile.coords in self.tiles_in_rack:
            self.tiles_in_rack[other_tile.coords] = other_tile

        elif other_tile.coords in self.tiles_to_exchange:
            self.tiles_in_rack[other_tile.coords] = other_tile

    def on_tile_move(self, tile):
        x, y = tile.coords.get()

        if y == 15 or (y in (16, 17) and not 2 < x < 12) or self.is_ai_turn:
            tile.undo_move()
            return

        other_tile = None
        dicts_to_check = [self.latest_tiles, self.tiles_in_rack, self.tiles_to_exchange]
        for dict_to_check in dicts_to_check:
            if tile.coords in dict_to_check:
                other_tile = dict_to_check.get(tile.coords)
                break

        if other_tile:
            self.swap_tiles(tile, other_tile)

        elif self.tiles.get(tile.coords):
            tile.undo_move()
            return

        else:
            del self.tiles[tile.old_coords]
            if tile.old_coords.y() == 16:
                del self.tiles_in_rack[tile.old_coords]

            elif tile.old_coords.y() == 17:
                del self.tiles_to_exchange[tile.old_coords]

            else:
                del self.latest_tiles[tile.old_coords]

            self.tiles[tile.coords] = tile
            if y == 16:
                self.tiles_in_rack[tile.coords] = tile
            elif y == 17:
                self.tiles_to_exchange[tile.coords] = tile
            else:
                self.latest_tiles[tile.coords] = tile

    def build_board_scene(self):
        self.build_squares()
        self.build_bonus_fields()
        self.build_rack()
        self.build_exchange_zone()
        self.build_labels()

    def build_squares(self):

        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)

        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                square = self.add_square(row, column, pen, brush)
                self.squares[Coords(row, column)] = square

    def build_bonus_fields(self):
        for bonus_field in self.bonus_fields:
            brush = bonus_field["Brush"]
            pen = bonus_field["Pen"]
            bonus_fields = []

            for position in bonus_field["Positions"]:
                square = self.squares[position]
                square.setZValue(2)
                bonus_fields.append(square)

            paint_graphic_items(bonus_fields, pen, brush)

    def build_rack(self):
        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        for column in range(4, 12):
            self.add_square(16, column, pen, brush)

    def build_exchange_zone(self):
        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        for column in range(4, 12):
            self.add_square(17, column, pen, brush)

        position = QPointF(64, 712)
        label = QGraphicsSimpleTextItem('Litery do wymiany →')
        label.setPos(position)
        self.scene.addItem(label)

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

        triple_word_bonuses = {
            "Name": "triple word",
            "Pen": QPen(Qt.darkRed, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(255, 0, 0, 180)),
            "Positions": triple_word_bonus_coords
        }
        self._triple_word_bonuses = triple_word_bonus_coords
        self.bonus_fields.append(triple_word_bonuses)

        double_word_bonuses = {
            "Name": "double word",
            "Pen": QPen(Qt.red, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(255, 0, 0, 100)),
            "Positions": double_word_bonus_coords
        }
        self._double_word_bonuses = double_word_bonus_coords
        self.bonus_fields.append(double_word_bonuses)

        triple_letter_bonuses = {
            "Name": "triple letter",
            "Pen": QPen(Qt.darkBlue, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(0, 0, 255, 180)),
            "Positions": triple_letter_bonus_coords
        }
        self._triple_letter_bonuses = triple_letter_bonus_coords
        self.bonus_fields.append(triple_letter_bonuses)

        double_letter_bonuses = {
            "Name": "double letter",
            "Pen": QPen(Qt.blue, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(0, 0, 255, 100)),
            "Positions": double_letter_bonus_coords
        }
        self._double_letter_bonuses = double_letter_bonus_coords
        self.bonus_fields.append(double_letter_bonuses)
