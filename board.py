import threading
from dictionary import is_word_in_dictionary
from tile import *
from sack import *
from ai import *
import time
import random


class Board(QGraphicsView):
    def __init__(self, score, player_clock, ai_clock, set_comment, text_field, set_prompt, confirm_button,
                 end_turn_button, exchange_button):
        QGraphicsView.__init__(self)

        self.ROWS = 15
        self.COLUMNS = 15

        self.squares = {}
        self.bonus_fields = []
        self._double_word_bonuses = []
        self._triple_word_bonuses = []
        self._double_letter_bonuses = []
        self._triple_letter_bonuses = []

        self.create_bonus_fields()
        self.scene = QGraphicsScene()
        self.build_board_scene()
        self.scene.setSceneRect(-SQUARE_SIZE / 2, -SQUARE_SIZE / 2, SQUARE_SIZE * 16, SQUARE_SIZE * 19)
        self.setMinimumSize(int(self.scene.width()) + SQUARE_SIZE, int(self.scene.height()) + SQUARE_SIZE)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setScene(self.scene)
        self.player_clock = player_clock
        self.ai_clock = ai_clock
        self.set_comment = set_comment
        self.set_prompt = set_prompt
        self.exchange_button = exchange_button
        self.end_turn_button = end_turn_button
        self.confirm_button = confirm_button
        self.text_field = text_field

        # parameters visible for AI
        # tiles represent all tiles on board
        self.tiles = None
        # sack represents sack
        self.sack = None

        # score represents total score of both players
        self.score = score
        # latest tiles represent tiles added in last turn
        self.latest_tiles = None
        self.tiles_in_rack = None
        self.tiles_to_exchange = None
        self._total_points = None
        self._points = None
        self._words = None
        self._is_connected = False
        self.ai = None
        self.ai_thread = None

    def prepare_game(self):
        self.sack = Sack()
        self.tiles = {}
        self.latest_tiles = {}
        self.tiles_in_rack = {}
        self.tiles_to_exchange = {}
        self.ai = AI(self.tiles, self.sack)
        self._total_points = 0
        self._points = 0
        self._words = []
        self._is_connected = False

    def start_game(self):
        self.prepare_game()
        # self.ai_ = bool(random.getrandbits(1))
        self.ai.is_turn = False
        self.add_letters_to_rack()
        self.ai.finished.connect(self.end_of_ai_turn)
        self.ai.start()
        if self.ai.is_turn:
            self.set_comment('Przeciwnik myśli')

        else:
            self.player_clock.start()
        return self.ai.is_turn

    def add_letters_to_rack(self, letters=None):
        if not letters:
            letters = self.sack.draw(7 - len(self.tiles_in_rack) - len(self.tiles_to_exchange))
        index = 0
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND):
            coords = Coords(column, RACK_ROW)
            if not self.tiles.get(coords) and len(self.tiles_in_rack) + len(self.tiles_to_exchange) < 7:
                letter = letters[index]
                index += 1

                coords = Coords(column, RACK_ROW)
                points = get_value(letter)
                tile = Tile(letter, points, coords, self.on_tile_move)
                self.scene.addItem(tile)
                self.tiles_in_rack[coords] = tile
                self.tiles[coords] = tile

    def exchange_letters(self):
        if self.ai.is_turn:
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

        self.score.add_points('Gracz', 0)
        self.start_of_ai_turn()

    def resign(self):
        for tile in self.tiles.values():
            self.scene.removeItem(tile)

        self.prepare_game()

    def start_of_ai_turn(self):
        self.player_clock.stop()
        self.ai_clock.start()
        self.ai.is_turn = True
        self.exchange_button.setDisabled(True)
        self.end_turn_button.setDisabled(True)

    def end_of_ai_turn(self):
        self.ai_clock.stop()
        self.end_turn_button.setDisabled(False)
        self.exchange_button.setDisabled(False)

        word = self.ai.word

        for letter, points, coords in word.added_letters:
            tile = Tile(letter, points, coords)
            tile.set_immovable()
            self.tiles[coords] = tile
            self.scene.addItem(tile)
            tile.update()

        self.set_comment(f'Komputer ułożył słowo {word} i uzyskał {word.sum_up()} punktów')
        self.score.add_points('AI', word.sum_up())

        self.player_clock.start()

    def end_turn(self):
        if self.ai.is_turn:
            self.set_comment('Ruch przeciwnika')
            return

        blank_tiles = []
        column = row = -1
        columns = []
        rows = []
        self._is_connected = True

        if not self.latest_tiles:
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
                if new_letter.upper() in values_without_blank():
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

            is_valid = True

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
                    is_valid = False

            if column >= 0:
                if column == x:
                    rows.append(y)
                else:
                    is_valid = False

            if row >= 0:
                if row == y:
                    columns.append(x)
                else:
                    is_valid = False

            if not is_valid:
                self.set_comment('Wyrazy muszą być ułożone w jednej linii')
                return

        self._words = []
        self._points = 0

        if rows:
            self.add_word_and_points(column, rows[0], Directions.down, min(rows), max(rows))

            for row in rows:
                self.add_word_and_points(column, row, Directions.right)

        elif columns:
            self.add_word_and_points(columns[0], row, Directions.right, min(columns), max(columns))

            for column in columns:
                self.add_word_and_points(column, row, Directions.down)

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

        self.player_clock.stop()
        for tile_coords in self.latest_tiles.values():
            tile_coords.set_immovable()

        if self.sack.how_many_remain() and not self.tiles_in_rack and not self.tiles_to_exchange:
            self._points += 50

        self.set_comment(f'ułożyłeś słowa {self._words} i uzyskałeś {self._points} punktów')

        self.score.add_points('Gracz', self._points)
        self.add_letters_to_rack()

        self.start_of_ai_turn()

        self.latest_tiles.clear()

    def add_word_and_points(self, column, row, direction, first=None, last=None):
        word = ''
        word_points = 0
        word_multiplier = 1

        if direction == Directions.right:
            if not first:
                first = column
            if not last:
                last = column

            while self.tiles.get(Coords(first - 1, row)):
                first -= 1
            while self.tiles.get(Coords(last + 1, row)):
                last += 1

        elif direction == Directions.down:
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
            if direction == Directions.right:
                coords = Coords(current, row)
            elif direction == Directions.down:
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

        if tile.coords.is_in_rack():
            self.tiles_in_rack[tile.coords] = tile

        elif tile.coords.is_in_exchange_zone():
            self.tiles_to_exchange[tile.coords] = tile

        else:
            self.latest_tiles[tile.coords] = tile

        if other_tile.coords.is_in_rack():
            self.tiles_in_rack[other_tile.coords] = other_tile

        elif other_tile.coords.is_in_exchange_zone():
            self.tiles_in_rack[other_tile.coords] = other_tile

        else:
            self.latest_tiles[other_tile.coords] = other_tile

    def on_tile_move(self, tile):
        if not tile.coords.is_valid():
            tile.undo_move()
            return
        if tile.coords.is_on_board() and self.ai.is_turn:
            self.set_comment('Ruch przeciwnika')
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
            if tile.old_coords.is_in_rack():
                del self.tiles_in_rack[tile.old_coords]

            elif tile.old_coords.is_in_exchange_zone():
                del self.tiles_to_exchange[tile.old_coords]

            else:
                del self.latest_tiles[tile.old_coords]

            self.tiles[tile.coords] = tile
            if tile.coords.is_in_rack():
                self.tiles_in_rack[tile.coords] = tile
            elif tile.coords.is_in_exchange_zone():
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
                x, y = position.get()
                field_name = QGraphicsSimpleTextItem(bonus_field["Name"])
                font = field_name.font()
                font.setPointSize(10)
                fm = QFontMetrics(font)
                field_name.setFont(font)
                field_name.setX(x * SQUARE_SIZE + (SQUARE_SIZE - fm.width(bonus_field["Name"])) / 2)
                field_name.setY(y * SQUARE_SIZE + (SQUARE_SIZE - fm.height()) / 2)

                self.scene.addItem(field_name)

            paint_graphic_items(bonus_fields, pen, brush)

    def build_rack(self):
        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND + 1):
            self.add_square(RACK_ROW, column, pen, brush)

    def build_exchange_zone(self):
        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND + 1):
            self.add_square(EXCHANGE_ROW, column, pen, brush)

        position = QPointF(34, 690)
        label = QGraphicsSimpleTextItem('Litery do wymiany →')
        label.setPos(position)
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
        fm = QFontMetrics(QGraphicsSimpleTextItem().font())
        for count in range(LAST_ROW + 1):
            number = str(count + 1)
            number_label = QGraphicsSimpleTextItem(number)
            number_position = QPointF(-fm.width(number) - 2 * MARGIN,
                                      count * SQUARE_SIZE + (SQUARE_SIZE - fm.height()) / 2)
            number_label.setPos(number_position)

            letter = chr(count + ord('A'))
            letter_label = QGraphicsSimpleTextItem(letter)
            letter_position = QPointF(count * SQUARE_SIZE + (SQUARE_SIZE - fm.width(letter)) / 2,
                                      -fm.height() - MARGIN)
            letter_label.setPos(letter_position)

            self.scene.addItem(number_label)
            self.scene.addItem(letter_label)

    def create_bonus_fields(self):

        triple_word_bonuses = {
            "Name": "3S",
            "Pen": QPen(Qt.darkRed, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(255, 0, 0, 160)),
            "Positions": triple_word_bonus_coords
        }
        self._triple_word_bonuses = triple_word_bonus_coords
        self.bonus_fields.append(triple_word_bonuses)

        double_word_bonuses = {
            "Name": "2S",
            "Pen": QPen(Qt.red, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(255, 0, 0, 100)),
            "Positions": double_word_bonus_coords
        }
        self._double_word_bonuses = double_word_bonus_coords
        self.bonus_fields.append(double_word_bonuses)

        triple_letter_bonuses = {
            "Name": "3L",
            "Pen": QPen(Qt.darkBlue, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(0, 0, 255, 160)),
            "Positions": triple_letter_bonus_coords
        }
        self._triple_letter_bonuses = triple_letter_bonus_coords
        self.bonus_fields.append(triple_letter_bonuses)

        double_letter_bonuses = {
            "Name": "2L",
            "Pen": QPen(Qt.blue, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(QColor(0, 0, 255, 100)),
            "Positions": double_letter_bonus_coords
        }
        self._double_letter_bonuses = double_letter_bonus_coords
        self.bonus_fields.append(double_letter_bonuses)
