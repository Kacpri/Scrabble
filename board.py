from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QFontMetrics, QPen, QFont
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsSimpleTextItem

from naive_ai import NaiveAI
from tile import Tile
from sack import Sack
from ai import AI
from dictionary import Dictionary
from colors import *
from constants import *
from board_utils import *
from random import getrandbits


class Board(QGraphicsView):
    def __init__(self, score, player_clock, ai_clock, add_comment, set_prompt, sack_counter):
        QGraphicsView.__init__(self)

        self.scale = 1

        self._board_squares = {}
        self._other_squares = {}
        self._bonus_fields = []
        self._labels = {}

        self.scene = QGraphicsScene()
        self.build_board_scene()
        self.prepare_board()
        self.setScene(self.scene)

        self.naive_ai_clock = player_clock
        self.ai_clock = ai_clock
        self.add_info = add_comment
        self.set_prompt = set_prompt

        self.is_game_started = False

        # parameters visible for AI
        self.tiles_for_ai = {}
        self.tiles_for_naive_ai = {}
        # sack represents sack
        self.sack = None

        self.sack_counter = sack_counter
        # score represents total score of both players
        self.score = score
        # tiles represent all tiles on board
        self._tiles = {}
        # latest tiles represent tiles added in last turn
        self.new_tiles = {}
        self._latest_tiles = set()
        self._tiles_in_rack = set()
        self._tiles_to_exchange = set()
        self._blanks = []
        self._points = 0
        self._words = []
        self._is_connected = False
        self.ai = None
        self.naive_ai = None

    def auto_resize(self):
        if self.height() / self.width() < DEFAULT_HEIGHT / DEFAULT_WIDTH:
            scale = round(self.height() / DEFAULT_HEIGHT, 1)
        else:
            scale = round(self.width() / DEFAULT_WIDTH, 1)

        if abs(scale - self.scale) < 0.0001:
            return
        self.scale = scale

        self.scene.setSceneRect(-SQUARE_SIZE / 2, -SQUARE_SIZE / 2, SQUARE_SIZE * 16 * self.scale,
                                SQUARE_SIZE * 19 * self.scale)
        for tile in self._tiles.values():
            tile.resize(self.scale)
        for square in self._board_squares.values():
            square.setScale(self.scale)
        for square in self._other_squares.values():
            square.setScale(self.scale)
        for x, y in self._labels:
            label = self._labels.get((x, y))
            label.setScale(self.scale)
            label.setPos(x * self.scale, y * self.scale)

    def prepare_game(self):
        self.sack = Sack(self.sack_counter)
        self.ai = AI(self.tiles_for_ai, self.sack)
        self.naive_ai = NaiveAI(self.tiles_for_naive_ai, self.sack)

    def reset_game(self):
        self.is_game_started = False
        self.ai.stop()
        self.naive_ai.stop()

        for tile in self._tiles.values():
            self.scene.removeItem(tile)

        self.tiles_for_ai.clear()
        self.tiles_for_naive_ai.clear()
        self._tiles.clear()
        self._latest_tiles.clear()
        self._tiles_in_rack.clear()
        self._tiles_to_exchange.clear()
        self._blanks.clear()
        self._words.clear()
        self._points = 0
        self._is_connected = False
        self.prepare_game()

    def start_game(self):
        if self.is_game_started:
            self.reset_game()
        self.prepare_game()
        self.is_game_started = True
        self.ai.is_turn = bool(getrandbits(1))
        self.naive_ai.is_turn = not self.ai.is_turn
        # self.add_letters_to_rack()
        self.ai.finished.connect(self.end_ai_turn)
        self.naive_ai.finished.connect(self.end_naive_ai_turn)
        self.ai.start()
        self.naive_ai.start()
        if self.ai.is_turn:
            self.start_ai_turn()
        else:
            self.start_naive_ai_turn()
            self.naive_ai_clock.start()

    def move_to_rack(self, tile):
        old_coords = tile.coords
        if old_coords in self._tiles_in_rack:
            return

        coords = Coords(LEFT_RACK_BOUND, RACK_ROW)
        while coords in self._tiles_in_rack:
            coords = coords.move(RIGHT)

        if old_coords in self._tiles_to_exchange:
            self._tiles_to_exchange.remove(old_coords)
        else:
            self._latest_tiles.remove(old_coords)

        del self._tiles[old_coords]
        self._tiles[coords] = tile
        self._tiles_in_rack.add(coords)
        tile.move_to_coords(coords)

    def collect_tiles(self):
        for coords in set.union(self._latest_tiles, self._tiles_to_exchange):
            tile = self.get_tile(coords)
            self.move_to_rack(tile)

    def skip_turn(self):
        self.collect_tiles()
        self.score.add_points('SI bez ewaluacji', '(Pominięcie ruchu)', 0)
        self.start_ai_turn()

    def naive_ai_ends(self):
        points = 0
        letters = ' '
        for letter in self.ai.rack:
            points += Sack.get_value(letter)
            letters += f'{letter}, '
        self.score.add_points('SI bez ewaluacji', '', points)
        self.score.add_points('SI z ewaluacją', f'(Zostały {letters[:-2]})', -points)
        self.end_game()

    def ai_ends(self):
        points = 0
        letters = ' '
        for letter in self.naive_ai.rack:
            points += Sack.get_value(letter)
            letters += f'{letter}, '

        self.score.add_points('SI bez ewaluacji', f'(Zostały {letters[:-2]})', -points)
        self.score.add_points('SI z ewaluacją', '', points)
        self.end_game()

    def end_game(self):
        player_score = self.score.get_score('SI bez ewaluacji')
        ai_score = self.score.get_score('SI z ewaluacją')
        if player_score > ai_score:
            self.add_info('Gratulacje! Udało Ci się pokonać algorytm!')
        elif player_score < ai_score:
            self.add_info('Tym razem się nie udało. Próbuj dalej :)')
        else:
            self.add_info('Dobry remis nie jest zły ;)')

    def start_naive_ai_turn(self):
        for coords in self.new_tiles:
            self.tiles_for_naive_ai[coords] = self.get_tile(coords)
        self.new_tiles.clear()

        self.naive_ai.is_turn = True
        self.naive_ai_clock.start()

    def start_ai_turn(self):
        for coords in self.new_tiles:
            self.tiles_for_ai[coords] = self.get_tile(coords)
        self.new_tiles.clear()

        self.ai.is_turn = True
        self.ai_clock.start()

    def end_naive_ai_turn(self):
        if not self.is_game_started:
            return

        self.naive_ai_clock.stop()

        word = self.naive_ai.word
        words = [word]

        if word:
            for coords in word.added_letters:
                letter, points = word.added_letters.get(coords)
                tile = Tile(letter, points, coords, self.scale)
                tile.place()
                tile.remove_highlight()
                self._tiles[coords] = tile
                self.scene.addItem(tile)
                self.new_tiles[coords] = tile
                perpendicular_word = self.find_word(coords, ~word.direction(), False)
                if perpendicular_word:
                    words.append(perpendicular_word)

            self.score.add_points('SI bez ewaluacji', words, word.sum_up())

        else:
            self.add_info(f'Komputer wymienił litery')
            self.score.add_points('SI bez ewaluacji', '(wymiana liter)', 0)

        if not self.naive_ai.rack:
            self.naive_ai_ends()
            return

        self.start_ai_turn()

    def end_ai_turn(self):
        if not self.is_game_started:
            return

        self.ai_clock.stop()

        word = self.ai.word
        words = [word]

        if word:
            for coords in word.added_letters:
                letter, points = word.added_letters.get(coords)
                tile = Tile(letter, points, coords, self.scale)
                tile.place()
                self._tiles[coords] = tile
                self.scene.addItem(tile)
                self.new_tiles[coords] = tile
                perpendicular_word = self.find_word(coords, ~word.direction(), False)
                if perpendicular_word:
                    words.append(perpendicular_word)

            self.score.add_points('SI z ewaluacją', words, word.sum_up())

        else:
            self.add_info(f'Komputer wymienił litery')
            self.score.add_points('SI z ewaluacją', '(wymiana liter)', 0)

        if not self.ai.rack:
            self.ai_ends()
            return

        self.start_naive_ai_turn()

    def wait_for_blank(self, blank):
        self._blanks.append(blank)
        self.set_prompt("Jaką literą ma być blank?")
        self.confirm_button.setDisabled(False)

    def stop_waiting_for_blank(self):
        self.set_prompt('')
        self.confirm_button.setDisabled(True)

    def find_word(self, coords, direction, is_players_turn=True):
        word = ''
        word_points = 0
        word_multiplier = 1
        direction = abs(direction)

        first_tile = coords
        while self.get_tile(first_tile.move(-direction)):
            first_tile = first_tile.move(-direction)

        last_tile = coords
        while self.get_tile(last_tile.move(direction)):
            last_tile = last_tile.move(direction)

        if first_tile == last_tile:
            return

        current_tile = first_tile
        while current_tile <= last_tile:
            tile = self.get_tile(current_tile)
            points = tile.points

            if not tile.is_placed:
                if current_tile in double_letter_bonuses:
                    points *= 2
                elif current_tile in triple_letter_bonuses:
                    points *= 3
                elif current_tile in double_word_bonuses:
                    word_multiplier *= 2
                elif current_tile in triple_word_bonuses:
                    word_multiplier *= 3

            word_points += points
            word += tile.letter

            current_tile = current_tile.move(direction)

        if is_players_turn:
            self._words.append(word)
            self._points += word_points * word_multiplier
        else:
            return word

    def get_tile(self, coords: Coords) -> Tile:
        return self._tiles.get(coords)

    def build_board_scene(self):
        self.build_squares()
        self.prepare_bonus_fields()
        self.build_bonus_fields()
        self.build_rack()
        self.build_exchange_zone()
        self.build_labels()

    def build_squares(self):
        brush = QBrush(LIGHT_SEA_GREEN)
        pen = QPen(DARK_SEA_GREEN, 1, Qt.SolidLine)

        for row in range(LAST_ROW + 1):
            for column in range(LAST_COLUMN + 1):
                square = self.add_square(row, column, pen, brush)
                self._board_squares[Coords(row, column)] = square

    def build_bonus_fields(self):
        for bonus_field in self._bonus_fields:
            brush = bonus_field["Brush"]
            pen = bonus_field["Pen"]
            bonus_fields = []

            for coords in bonus_field["Coords"]:
                label = bonus_field["Name"]
                if coords == Coords.central():
                    label = '✸'
                square = self._board_squares[coords]
                square.setZValue(2)
                bonus_fields.append(square)
                field_name = QGraphicsSimpleTextItem(label)
                font = field_name.font()
                font.setPointSize(10)
                if coords == Coords.central():
                    font.setPointSize(20)
                fm = QFontMetrics(font)
                field_name.setZValue(2.1)
                field_name.setFont(font)
                x = coords.x * SQUARE_SIZE + (SQUARE_SIZE - fm.width(label)) / 2
                y = coords.y * SQUARE_SIZE + (SQUARE_SIZE - fm.height()) / 2
                field_name.setPos(x, y)
                field_name.setBrush(bonus_field["Label brush"])

                self._labels[(x, y)] = field_name
                self.scene.addItem(field_name)

            paint_graphic_items(bonus_fields, pen, brush)

    def build_rack(self):
        brush = QBrush(LIGHT_BROWN)
        pen = QPen(BROWN, 1, Qt.SolidLine)
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND + 1):
            square = self.add_square(RACK_ROW, column, pen, brush)
            self._other_squares[Coords(column, RACK_ROW)] = square

    def build_exchange_zone(self):
        brush = QBrush(LIGHT_BROWN)
        pen = QPen(BROWN, 1, Qt.SolidLine)
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND + 1):
            square = self.add_square(EXCHANGE_ROW, column, pen, brush)
            self._other_squares[Coords(column, EXCHANGE_ROW)] = square

        text = 'Litery do wymiany →     '
        font = QFont('Verdana', 10)
        fm = QFontMetrics(font)
        x = SQUARE_SIZE * LEFT_RACK_BOUND - fm.width(text)
        y = SQUARE_SIZE * EXCHANGE_ROW + (SQUARE_SIZE - fm.height()) / 2
        label = QGraphicsSimpleTextItem(text)
        label.setPos(x, y)
        label.setFont(font)
        label.setBrush(QBrush(Qt.white))
        self._labels[(x, y)] = label
        self.scene.addItem(label)

    def add_square(self, row, column, pen, brush):
        height = SQUARE_SIZE
        width = SQUARE_SIZE

        column_distance = column * width
        row_distance = row * height

        x = column_distance
        y = row_distance
        rectangle = QRectF(x, y, width, height)

        return self.scene.addRect(rectangle, pen, brush)

    def build_labels(self):
        font = QFont('Verdana', 10)
        fm = QFontMetrics(font)
        for count in range(LAST_ROW + 1):
            number = str(count + 1)
            number_label = QGraphicsSimpleTextItem(number)
            x = -fm.width(number) - SQUARE_SIZE / 8
            y = count * SQUARE_SIZE + (SQUARE_SIZE - fm.height()) / 2
            number_label.setPos(x, y)
            number_label.setFont(font)
            number_label.setBrush(QBrush(Qt.white))
            self._labels[(x, y)] = number_label

            letter = chr(count + ord('A'))
            letter_label = QGraphicsSimpleTextItem(letter)
            x = count * SQUARE_SIZE + (SQUARE_SIZE - fm.width(letter)) / 2
            y = -fm.height() - SQUARE_SIZE / 8
            letter_label.setPos(x, y)
            letter_label.setFont(font)
            letter_label.setBrush(QBrush(Qt.white))
            self._labels[(x, y)] = letter_label

            self.scene.addItem(number_label)
            self.scene.addItem(letter_label)

    def prepare_bonus_fields(self):

        triple_word_bonus_fields = {
            "Name": "3S",
            "Pen": QPen(DARK_RED, 1, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin),
            "Brush": QBrush(RED),
            "Label brush": QBrush(DARK_RED),
            "Coords": triple_word_bonuses
        }
        self._bonus_fields.append(triple_word_bonus_fields)

        double_word_bonus_fields = {
            "Name": "2S",
            "Pen": QPen(RED, 1, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin),
            "Brush": QBrush(PINK),
            "Label brush": QBrush(RED),
            "Coords": double_word_bonuses
        }
        self._bonus_fields.append(double_word_bonus_fields)

        triple_letter_bonus_fields = {
            "Name": "3L",
            "Pen": QPen(NAVY_BLUE, 1, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin),
            "Brush": QBrush(BLUE),
            "Label brush": QBrush(NAVY_BLUE),
            "Coords": triple_letter_bonuses
        }
        self._bonus_fields.append(triple_letter_bonus_fields)

        double_letter_bonus_fields = {
            "Name": "2L",
            "Pen": QPen(BLUE2, 1, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin),
            "Brush": QBrush(LIGHT_BLUE),
            "Label brush": QBrush(BLUE2),
            "Coords": double_letter_bonuses
        }
        self._bonus_fields.append(double_letter_bonus_fields)

    def prepare_board(self):
        self.scene.setSceneRect(-SQUARE_SIZE / 2, -SQUARE_SIZE / 2, SQUARE_SIZE * 16, SQUARE_SIZE * 19)
        self.scene.setBackgroundBrush(QBrush(SEA_GREEN))
        self.setMinimumSize(MINIMAL_WIDTH, MINIMAL_HEIGHT)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
