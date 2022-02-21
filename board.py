from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QFontMetrics, QPen, QFont
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsSimpleTextItem

from tile import Tile
from sack import Sack
from ai import AI
from dictionary import Dictionary
from colors import *
from constants import *
from board_utils import *
from random import getrandbits


class Board(QGraphicsView):
    def __init__(self, score, player_clock, ai_clock, add_comment, text_field, set_prompt, confirm_button,
                 disable_buttons, sack_counter):
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

        self.player_clock = player_clock
        self.ai_clock = ai_clock
        self.add_info = add_comment
        self.set_prompt = set_prompt
        self.disable_buttons = disable_buttons
        self.confirm_button = confirm_button
        self.text_field = text_field

        self.is_game_started = False

        # parameters visible for AI
        self.tiles_for_ai = {}
        # sack represents sack
        self.sack = None

        self.sack_counter = sack_counter
        # score represents total score of both players
        self.score = score
        # tiles represent all tiles on board
        self._tiles = {}
        # latest tiles represent tiles added in last turn
        self.new_tiles = []
        self._latest_tiles = set()
        self._tiles_in_rack = set()
        self._tiles_to_exchange = set()
        self._blanks = []
        self._points = 0
        self._words = []
        self._is_connected = False
        self.ai = None

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
        self.is_game_started = False
        self.sack = Sack(self.sack_counter)
        self.ai = AI(self.tiles_for_ai, self.sack)

    def reset_game(self):
        for tile in self._tiles.values():
            self.scene.removeItem(tile)

        self.tiles_for_ai.clear()
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
        self.add_letters_to_rack()
        self.ai.finished.connect(self.end_ai_turn)
        self.ai.start()
        if self.ai.is_turn:
            self.add_info('Przeciwnik zaczyna')
            self.start_ai_turn()
        else:
            self.add_info('Zaczynasz')
            self.player_clock.start()

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
        self.score.add_points('Gracz', '(Pominięcie ruchu)', 0)
        self.start_ai_turn()

    def player_ends(self):
        self.player_clock.stop()
        points = 0
        letters = ' '
        for letter in self.ai.rack:
            points += Sack.get_value(letter)
            letters += f'{letter}, '

        self.score.add_points('AI', f'(Zostały {letters[:-2]})', -points)
        self.score.add_points('Gracz', '', points)
        self.end_game()

    def ai_ends(self):
        points = 0
        letters = ' '
        for coords in self._tiles_in_rack:
            tile = self.get_tile(coords)
            points += tile.points
            letters += f'{tile.letter}, '
        for coords in self._tiles_to_exchange:
            tile = self.get_tile(coords)
            points += tile.points
            letters += f'{tile.letter}, '

        self.score.add_points('Gracz', f'(Zostały {letters[:-2]})', -points)
        self.score.add_points('AI', '', points)
        self.end_game()

    def end_game(self):
        player_score = self.score.get_score('Gracz')
        ai_score = self.score.get_score('AI')
        if player_score > ai_score:
            self.add_info('Gratulacje! Udało Ci się pokonać algorytm!')
        elif player_score < ai_score:
            self.add_info('Tym razem się nie udało. Próbuj dalej :)')
        else:
            self.add_info('Dobry remis nie jest zły ;)')

    def add_letters_to_rack(self, letters=None):
        if not letters:
            letters = self.sack.draw(MAX_RACK_SIZE - len(self._tiles_in_rack) - len(self._tiles_to_exchange))

        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND + 1):
            if not letters:
                return
            coords = Coords(column, RACK_ROW)
            if not self.get_tile(coords) and len(self._tiles_in_rack) + len(self._tiles_to_exchange) < MAX_RACK_SIZE:
                letter = letters.pop()

                coords = Coords(column, RACK_ROW)
                points = Sack.get_value(letter)
                tile = Tile(letter, points, coords, self.scale, self.on_tile_move, self.move_to_rack)
                self.scene.addItem(tile)
                self._tiles_in_rack.add(coords)
                self._tiles[coords] = tile

    def exchange_letters(self):
        if self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            return

        if not self._tiles_to_exchange:
            self.add_info('Brak liter do wymiany')
            return

        letters_to_exchange = []
        for coords in self._tiles_to_exchange:
            tile = self.get_tile(coords)
            letters_to_exchange.append(tile.letter)
            del self._tiles[tile.coords]
            self.scene.removeItem(tile)

        letters_on_board = []
        for coords in self._latest_tiles:
            tile = self.get_tile(coords)
            letters_on_board.append(tile.letter)
            del self._tiles[tile.coords]
            self.scene.removeItem(tile)

        self._tiles_to_exchange.clear()
        self._latest_tiles.clear()

        new_letters = self.sack.exchange(letters_to_exchange)
        self.score.add_points('Gracz', '(wymiana liter)', 0)

        if not new_letters:
            self.add_info('Za mało płytek w worku')
            self.add_letters_to_rack(letters_to_exchange + letters_on_board)
            return

        self.add_info('Wymieniłeś/aś litery')
        self.add_letters_to_rack(new_letters + letters_on_board)

        self.start_ai_turn()

    def start_ai_turn(self):
        self.player_clock.stop()
        self.tiles_for_ai.clear()
        for coords in self._latest_tiles:
            self.tiles_for_ai[coords] = self.get_tile(coords)

        for tile in self.new_tiles:
            tile.remove_highlight()
        self.new_tiles.clear()

        self.ai.is_turn = True
        self.ai_clock.start()
        self.disable_buttons(True)

    def end_ai_turn(self):
        self.ai_clock.stop()
        self.disable_buttons(False)

        word = self.ai.word
        words = [word]

        for coords in self._latest_tiles:
            tile = self.get_tile(coords)
            tile.remove_highlight()

        self._latest_tiles.clear()

        if word:
            for coords in word.added_letters:
                letter, points = word.added_letters.get(coords)
                tile = Tile(letter, points, coords, self.scale)
                tile.place()
                self._tiles[coords] = tile
                self.scene.addItem(tile)
                self.new_tiles.append(tile)
                perpendicular_word = self.find_word(coords, ~word.direction(), False)
                if perpendicular_word:
                    words.append(perpendicular_word)

            self.score.add_points('AI', words, word.sum_up())

        else:
            self.add_info(f'Komputer wymienił litery')
            self.score.add_points('AI', '(wymiana liter)', 0)

        if not self.ai.rack:
            self.ai_ends()
            return

        self.player_clock.start()

    def wait_for_blank(self, blank):
        self._blanks.append(blank)
        self.set_prompt("Jaką literą ma być blank?")
        self.text_field.setDisabled(False)
        self.confirm_button.setDisabled(False)
        self.disable_buttons(True)

    def stop_waiting_for_blank(self):
        self.set_prompt('')
        self.text_field.setDisabled(True)
        self.text_field.clear()
        self.confirm_button.setDisabled(True)
        self.disable_buttons(False)

    def revert_blanks(self):
        for blank in self._blanks:
            blank.change_back()
        self._blanks.clear()
        self.stop_waiting_for_blank()

    def blank_entered(self):
        tile = self._blanks[-1]
        new_letter = self.text_field.text()
        if new_letter.lower() in Sack.values_without_blank():
            tile.change_to_blank(new_letter)
            self.stop_waiting_for_blank()
            self.end_turn()
        else:
            self.add_info('Podaj poprawną literę')
            self.text_field.clear()
            return

    def end_turn(self):
        if self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            return

        self._is_connected = False

        if not self._latest_tiles:
            self.add_info('Musisz najpierw wykonać ruch')
            return

        if not self.get_tile(Coords.central()):
            self.add_info('Pierwszy wyraz musi przechodzić przez środek')
            return

        if Coords.central() in self._latest_tiles:
            self._is_connected = True
            if len(self._latest_tiles) == 1:
                self.add_info('Wyraz musi zawierać przynajmniej dwie litery')
                return

        first_tile_coords = min(self._latest_tiles)
        last_tile_coords = max(self._latest_tiles)

        if first_tile_coords.is_same_column(last_tile_coords):
            direction = DOWN
        else:
            direction = RIGHT

        if len(self._latest_tiles) == 1 and (self.get_tile(first_tile_coords.move(RIGHT)) or self.get_tile(
                first_tile_coords.move(RIGHT))):
            self._is_connected = True

        columns = set()
        rows = set()
        for tile in self._latest_tiles:
            columns.add(tile.x)
            rows.add(tile.y)

        if len(rows) > 1 and len(columns) > 1:
            self.add_info('Litery muszą być ułożone w jednej linii')
            return

        while self.get_tile(first_tile_coords.move(-direction)):
            first_tile_coords = first_tile_coords.move(-direction)

        while self.get_tile(last_tile_coords.move(direction)):
            last_tile_coords = last_tile_coords.move(direction)

        current_coords = first_tile_coords

        while current_coords <= last_tile_coords:
            tile = self.get_tile(current_coords)
            if not tile:
                self.add_info("Litery muszą należeć do tego samego wyrazu")
                return

            if tile.is_placed or self.get_tile(
                    current_coords.move(~direction)) or self.get_tile(
                    current_coords.move(-~direction)):
                self._is_connected = True

            if tile.letter == BLANK:
                self.wait_for_blank(tile)
                return

            current_coords = current_coords.move(direction)

        if not self._is_connected:
            self.add_info('Wyraz musi się stykać z występującymi już na planszy')
            return

        self._words.clear()
        self._points = 0

        self.find_word(first_tile_coords, direction)

        if len(columns) > 1:
            for column in columns:
                self.find_word(Coords(column, first_tile_coords.y), ~direction)

        else:
            for row in rows:
                self.find_word(Coords(first_tile_coords.x, row), ~direction)

        for word in self._words:
            if not Dictionary.is_word_in_dictionary(word):
                self.add_info(f'słowo "{word}" nie występuje w słowniku')
                if self._blanks:
                    self.revert_blanks()
                return

        for coords in self._latest_tiles:
            tile = self.get_tile(coords)
            tile.place()

        self._blanks.clear()

        if len(self._latest_tiles) == MAX_RACK_SIZE:
            self._points += 50

        self.score.add_points('Gracz', self._words, self._points)
        self.add_letters_to_rack()

        if not self._tiles_in_rack and not self._tiles_to_exchange and not self.sack.how_many_remain():
            self.player_ends()
            return

        self.start_ai_turn()

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

    def swap_tiles(self, tile, other_tile):
        tile.swap_with_other(other_tile)
        self._tiles[tile.coords] = tile
        self._tiles[other_tile.coords] = other_tile

    def on_tile_move(self, tile):
        if not tile.coords.is_valid():
            tile.undo_move()
            return
        if tile.coords.is_on_board() and self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            tile.undo_move()
            return

        other_tile = None
        if tile.coords in set.union(self._latest_tiles, self._tiles_in_rack, self._tiles_to_exchange):
            other_tile = self.get_tile(tile.coords)

        if other_tile:
            self.swap_tiles(tile, other_tile)

        elif self.get_tile(tile.coords):
            tile.undo_move()
            return

        else:
            del self._tiles[tile.old_coords]
            if tile.old_coords.is_in_rack():
                self._tiles_in_rack.remove(tile.old_coords)

            elif tile.old_coords.is_in_exchange_zone():
                self._tiles_to_exchange.remove(tile.old_coords)
            else:
                self._latest_tiles.remove(tile.old_coords)

            self._tiles[tile.coords] = tile
            if tile.coords.is_in_rack():
                self._tiles_in_rack.add(tile.coords)
            elif tile.coords.is_in_exchange_zone():
                self._tiles_to_exchange.add(tile.coords)
            else:
                self._latest_tiles.add(tile.coords)

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
