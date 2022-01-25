from dictionary import is_word_in_dictionary
from tile import *
from sack import *
from ai import *
from direction import Direction
from colors import *
from constants import DEFAULT_WIDTH, DEFAULT_HEIGHT, MINIMAL_WIDTH, MINIMAL_HEIGHT
import random


class Board(QGraphicsView):
    def __init__(self, score, player_clock, ai_clock, add_comment, text_field, set_prompt, confirm_button,
                 end_turn_button, exchange_button, sack_counter):
        QGraphicsView.__init__(self)

        self.scale = 1

        self._board_squares = {}
        self._other_squares = {}
        self._bonus_fields = []
        self._double_word_bonuses = []
        self._triple_word_bonuses = []
        self._double_letter_bonuses = []
        self._triple_letter_bonuses = []
        self._labels = {}

        self.create_bonus_fields()
        self.scene = QGraphicsScene()
        self.build_board_scene()
        self.scene.setSceneRect(-SQUARE_SIZE / 2, -SQUARE_SIZE / 2, SQUARE_SIZE * 16, SQUARE_SIZE * 19)
        self.scene.setBackgroundBrush(QBrush(SEA_GREEN))
        self.setMinimumSize(MINIMAL_WIDTH, MINIMAL_HEIGHT)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setScene(self.scene)
        self.player_clock = player_clock
        self.ai_clock = ai_clock
        self.add_info = add_comment
        self.set_prompt = set_prompt
        self.exchange_button = exchange_button
        self.end_turn_button = end_turn_button
        self.confirm_button = confirm_button
        self.text_field = text_field

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
        self._latest_tiles = {}
        self._tiles_in_rack = {}
        self._tiles_to_exchange = {}
        self._total_points = None
        self._points = None
        self._words = None
        self._is_connected = False
        self.ai = None
        self.ai_thread = None

    def resize(self):
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
        self.tiles_for_ai = {}
        self._tiles = {}
        self._latest_tiles = {}
        self._tiles_in_rack = {}
        self._tiles_to_exchange = {}
        self.ai = AI(self.tiles_for_ai, self.sack)
        self._total_points = 0
        self._points = 0
        self._words = []
        self._is_connected = False

    def start_game(self):
        self.prepare_game()
        self.ai.is_turns = bool(random.getrandbits(1))
        self.add_letters_to_rack()
        self.ai.finished.connect(self.end_of_ai_turn)
        self.ai.start()
        if self.ai.is_turn:
            self.add_info('Przeciwnik myśli')

        else:
            self.player_clock.start()
        return self.ai.is_turn

    def add_letters_to_rack(self, letters=None):
        if not letters:
            letters = self.sack.draw(7 - len(self._tiles_in_rack) - len(self._tiles_to_exchange))
        index = 0
        for column in range(LEFT_RACK_BOUND, RIGHT_RACK_BOUND):
            coords = Coords(column, RACK_ROW)
            if not self._tiles.get(coords) and len(self._tiles_in_rack) + len(self._tiles_to_exchange) < 7:
                letter = letters[index]
                index += 1

                coords = Coords(column, RACK_ROW)
                points = Sack.get_value(letter)
                tile = Tile(letter, points, coords, self.scale, self.on_tile_move)
                self.scene.addItem(tile)
                self._tiles_in_rack[coords] = tile
                self._tiles[coords] = tile

    def exchange_letters(self):
        if self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            return

        if not self._tiles_to_exchange:
            self.add_info('Brak liter do wymiany')
            return

        letters_to_exchange = []
        for tile in self._tiles_to_exchange.values():
            letters_to_exchange.append(tile.letter)
            del self._tiles[tile.coords]
            self.scene.removeItem(tile)

        letters_on_board = []
        for tile in self._latest_tiles.values():
            letters_on_board.append(tile.letter)
            del self._tiles[tile.coords]
            self.scene.removeItem(tile)

        self._tiles_to_exchange.clear()
        self._latest_tiles.clear()

        new_letters = self.sack.exchange(letters_to_exchange)
        self.score.add_points('Gracz', 0)

        if not new_letters:
            self.add_info('Za mało płytek w worku')
            self.add_letters_to_rack(letters_to_exchange + letters_on_board)
            return

        self.add_info('Wymieniłeś/aś litery')
        self.add_letters_to_rack(new_letters + letters_on_board)

        self.start_of_ai_turn()

    def resign(self):
        for tile in self._tiles.values():
            self.scene.removeItem(tile)

        self.prepare_game()

    def start_of_ai_turn(self):
        self.player_clock.stop()
        self.tiles_for_ai.clear()
        for coords in self._latest_tiles:
            self.tiles_for_ai[coords] = self._latest_tiles.get(coords)

        self.ai.is_turn = True
        self.ai_clock.start()
        self.exchange_button.setDisabled(True)
        self.end_turn_button.setDisabled(True)

    def end_of_ai_turn(self):
        self.ai_clock.stop()
        self.end_turn_button.setDisabled(False)
        self.exchange_button.setDisabled(False)

        word = self.ai.word

        if word:
            for letter, points, coords in word.added_letters:
                tile = Tile(letter, points, coords, self.scale)
                tile.place()
                self._tiles[coords] = tile
                self.scene.addItem(tile)
                tile.update()

            self.add_info(f'Komputer ułożył słowo "{word.lower()}" i uzyskał {word.sum_up()} punktów')
            self.score.add_points('AI', word.sum_up())

        else:
            self.add_info(f'Komputer wymienił litery')
            self.score.add_points('AI', 0)

        self.player_clock.start()

    def end_turn(self):
        if self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            return

        blank_tiles = []
        self._is_connected = False

        if not self._latest_tiles:
            self.add_info('Musisz najpierw wykonać ruch')
            return

        if not self._tiles.get(Coords.central()):
            self.add_info('Pierwszy wyraz musi przechodzić przez środek')
            return

        if self._latest_tiles.get(Coords.central()):
            self._is_connected = True
            if len(self._latest_tiles) == 1:
                self.add_info('Wyraz musi zawierać przynajmniej dwie litery')
                return

        sorted_latest_tiles = sorted(self._latest_tiles)
        first_tile_coords = sorted_latest_tiles[0]
        last_tile_coords = sorted_latest_tiles[-1]

        if first_tile_coords.is_same_column(last_tile_coords):
            direction = Direction.DOWN
        else:
            direction = Direction.RIGHT

        if self._tiles.get(first_tile_coords.on_right()) or self._tiles.get(
                first_tile_coords.on_left()) or self._tiles.get(first_tile_coords.above()) or self._tiles.get(
            first_tile_coords.below()):
            self._is_connected = True

        direct_coords, opposite_coords = Coords.get_functions(direction)
        perpendicular_coords, opposite_perpendicular_coords = Coords.get_functions(direction.perpendicular())

        columns = set()
        rows = set()
        for tile in sorted_latest_tiles:
            columns.add(tile.x)
            rows.add(tile.y)

        if len(rows) > 1 and len(columns) > 1:
            self.add_info('Litery muszą być ułożone w jednej linii')
            return

        while self._tiles.get(opposite_coords(first_tile_coords)):
            first_tile_coords = opposite_coords(first_tile_coords)

        while self._tiles.get(direct_coords(last_tile_coords)):
            last_tile_coords = direct_coords(last_tile_coords)

        current_coords = first_tile_coords

        while current_coords <= last_tile_coords:
            tile = self._tiles.get(current_coords)
            if not tile:
                self.add_info("Litery muszą należeć do tego samego wyrazu")
                return

            if tile.is_placed or self._tiles.get(perpendicular_coords(current_coords)) or self._tiles.get(
                    opposite_perpendicular_coords(current_coords)):
                self._is_connected = True

            if tile.letter == BLANK:
                self.set_prompt("Jaką literą ma być blank?")
                self.text_field.setDisabled(False)
                self.text_field.returnPressed.connect(self.end_turn)
                self.confirm_button.setDisabled(False)
                if not self.text_field.text():
                    return

                new_letter = self.text_field.text()
                if new_letter.upper() in Sack.values_without_blank():
                    tile.change_blank(new_letter.upper())
                    blank_tiles.append(tile)
                    self.text_field.setDisabled(True)
                    self.text_field.clear()
                    self.set_prompt('')
                    self.confirm_button.setDisabled(True)

                else:
                    self.add_info('Podaj poprawną literę')
                    self.text_field.clear()
                    return

            current_coords = direct_coords(current_coords)

        if not self._is_connected:
            self.add_info('Wyraz musi się stykać z występującymi już na planszy')
            return

        self._words = []
        self._points = 0

        self.add_word_and_points(first_tile_coords, direction)

        if len(columns) > 1:
            for column in columns:
                self.add_word_and_points(Coords(column, first_tile_coords.y), direction.perpendicular().opposite())

        else:
            for row in rows:
                self.add_word_and_points(Coords(first_tile_coords.x, row), direction.perpendicular().opposite())

        for word in self._words:
            if not is_word_in_dictionary(word):
                self.add_info(f'słowo "{word.lower()}" nie występuje w słowniku')
                if blank_tiles:
                    for blank in blank_tiles:
                        blank.change_back()
                    self.end_turn()
                return

        for tile_coords in self._latest_tiles.values():
            tile_coords.place()

        if len(self._latest_tiles) == 7:
            self._points += 50

        score_information = 'Ułożyłeś '
        for word in self._words:
            score_information += f'"{word.lower()}", '
        score_information += f' zdobyłeś {self._points} punktów'
        self.add_info(score_information)

        self.score.add_points('Gracz', self._points)
        self.add_letters_to_rack()

        self.start_of_ai_turn()

        self._latest_tiles.clear()

    def add_word_and_points(self, coords, direction):
        word = ''
        word_points = 0
        word_multiplier = 1

        direct_coords, opposite_coords = Coords.get_functions(direction)

        first_tile = coords
        while self._tiles.get(opposite_coords(first_tile)):
            first_tile = opposite_coords(first_tile)

        last_tile = coords
        while self._tiles.get(direct_coords(last_tile)):
            last_tile = direct_coords(last_tile)

        if first_tile == last_tile:
            return

        current_tile = first_tile
        while current_tile <= last_tile:
            tile = self._tiles.get(current_tile)
            if not tile:
                return
            points = tile.points

            if not tile.is_placed:
                if current_tile in self._double_letter_bonuses:
                    points *= 2
                elif current_tile in self._triple_letter_bonuses:
                    points *= 3
                elif current_tile in self._double_word_bonuses:
                    word_multiplier *= 2
                elif current_tile in self._triple_word_bonuses:
                    word_multiplier *= 3

            word_points += points
            word += tile.letter

            current_tile = direct_coords(current_tile)

        self._words.append(word)
        self._points += word_points * word_multiplier

    def swap_tiles(self, tile, other_tile):
        tile.swap_with_other(other_tile)
        self._tiles[tile.coords] = tile
        self._tiles[other_tile.coords] = other_tile

        if tile.coords.is_in_rack():
            self._tiles_in_rack[tile.coords] = tile

        elif tile.coords.is_in_exchange_zone():
            self._tiles_to_exchange[tile.coords] = tile

        else:
            self._latest_tiles[tile.coords] = tile

        if other_tile.coords.is_in_rack():
            self._tiles_in_rack[other_tile.coords] = other_tile

        elif other_tile.coords.is_in_exchange_zone():
            self._tiles_in_rack[other_tile.coords] = other_tile

        else:
            self._latest_tiles[other_tile.coords] = other_tile

    def on_tile_move(self, tile):
        if not tile.coords.is_valid():
            tile.undo_move()
            return
        if tile.coords.is_on_board() and self.ai.is_turn:
            self.add_info('Ruch przeciwnika')
            tile.undo_move()
            return

        other_tile = None
        dicts_to_check = [self._latest_tiles, self._tiles_in_rack, self._tiles_to_exchange]
        for dict_to_check in dicts_to_check:
            if tile.coords in dict_to_check:
                other_tile = dict_to_check.get(tile.coords)
                break

        if other_tile:
            self.swap_tiles(tile, other_tile)

        elif self._tiles.get(tile.coords):
            tile.undo_move()
            return

        else:
            del self._tiles[tile.old_coords]
            if tile.old_coords.is_in_rack():
                del self._tiles_in_rack[tile.old_coords]

            elif tile.old_coords.is_in_exchange_zone():
                del self._tiles_to_exchange[tile.old_coords]

            else:
                del self._latest_tiles[tile.old_coords]

            self._tiles[tile.coords] = tile
            if tile.coords.is_in_rack():
                self._tiles_in_rack[tile.coords] = tile
            elif tile.coords.is_in_exchange_zone():
                self._tiles_to_exchange[tile.coords] = tile
            else:
                self._latest_tiles[tile.coords] = tile

    def build_board_scene(self):
        self.build_squares()
        self.build_bonus_fields()
        self.build_rack()
        self.build_exchange_zone()
        self.build_labels()

    def build_squares(self):
        brush = QBrush(LIGHT_SEA_GREEN)
        pen = QPen(SEA_GREEN, 1, Qt.SolidLine)

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
                square = self._board_squares[coords]
                square.setZValue(2)
                bonus_fields.append(square)
                field_name = QGraphicsSimpleTextItem(bonus_field["Name"])
                font = field_name.font()
                font.setPointSize(10)
                fm = QFontMetrics(font)
                field_name.setZValue(2.1)
                field_name.setFont(font)
                x = coords.x * SQUARE_SIZE + (SQUARE_SIZE - fm.width(bonus_field["Name"])) / 2
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
        label.setBrush(QBrush(WHITE))
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
            number_label.setBrush(QBrush(WHITE))
            self._labels[(x, y)] = number_label

            letter = chr(count + ord('A'))
            letter_label = QGraphicsSimpleTextItem(letter)
            x = count * SQUARE_SIZE + (SQUARE_SIZE - fm.width(letter)) / 2
            y = -fm.height() - SQUARE_SIZE / 8
            letter_label.setPos(x, y)
            letter_label.setFont(font)
            letter_label.setBrush(QBrush(WHITE))
            self._labels[(x, y)] = letter_label

            self.scene.addItem(number_label)
            self.scene.addItem(letter_label)

    def create_bonus_fields(self):

        triple_word_bonuses = {
            "Name": "3S",
            "Pen": QPen(DARK_RED, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(RED),
            "Label brush": QBrush(DARK_RED),
            "Coords": triple_word_bonus_coords
        }
        self._triple_word_bonuses = triple_word_bonus_coords
        self._bonus_fields.append(triple_word_bonuses)

        double_word_bonuses = {
            "Name": "2S",
            "Pen": QPen(RED, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(PINK),
            "Label brush": QBrush(RED),
            "Coords": double_word_bonus_coords
        }
        self._double_word_bonuses = double_word_bonus_coords
        self._bonus_fields.append(double_word_bonuses)

        triple_letter_bonuses = {
            "Name": "3L",
            "Pen": QPen(NAVY_BLUE, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(BLUE),
            "Label brush": QBrush(NAVY_BLUE),
            "Coords": triple_letter_bonus_coords
        }
        self._triple_letter_bonuses = triple_letter_bonus_coords
        self._bonus_fields.append(triple_letter_bonuses)

        double_letter_bonuses = {
            "Name": "2L",
            "Pen": QPen(BLUE, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin),
            "Brush": QBrush(LIGHT_BLUE),
            "Label brush": QBrush(BLUE),
            "Coords": double_letter_bonus_coords
        }
        self._double_letter_bonuses = double_letter_bonus_coords
        self._bonus_fields.append(double_letter_bonuses)
