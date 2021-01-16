import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from sack import Sack
from tile import Tile
from board_utils import *


class Board(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.rows = 15
        self.columns = 15
        self.size = 4

        # self.deltaF = 1.0

        self.scale_manual = 10
        self.shift_focus = QPointF(0, 0)

        self.bonus_fields = []
        self.double_word_bonuses = []
        self.triple_word_bonuses = []
        self.double_letter_bonuses = []
        self.triple_letter_bonuses = []

        self.squares = {}
        self.tiles = {}
        self.adjacent_squares = {}
        self.sack = Sack()
        self.rack = []
        self.tiles_in_rack = {}
        self.tiles_added_in_current_turn = {}

        self.algorithm = Algorithm(self)

        self.total_points = 0
        self.points = 0
        self.words = []
        self.is_connected = False

        self.create_bonus_fields()
        self.scene = QGraphicsScene()
        self.build_board_scene()
        self.setScene(self.scene)

        self.button = QPushButton('Zakończ ruch', self)
        self.button.clicked.connect(self.end_turn)
        self.button.setStyleSheet("QPushButton { background-color: blue; color: white; font-size: 20px; "
                                  "margin-top: 7px; margin-left: 263px; padding: 3px}"
                                  "QPushButton:hover { background-color: navy }"
                                  "QPushButton:pressed { background-color: black }")

    # def wheelEvent(self, event):
    #     delta = event.angleDelta()
    #     self.deltaF = 1 + float(delta.y() / 1200)
    #     self.scale(self.deltaF, self.deltaF)

    def illegal_move(self):
        print(self.y())
        print('illegal moive')

    def add_word_and_points(self, column, row, direction, first=None, last=None):
        word = ''
        word_points = 0
        word_multiplier = 1

        if direction == 'horizontal':
            if not first:
                first = column
            if not last:
                last = column

            while self.tiles.get(f'{first - 1}-{row}'):
                first -= 1
            while self.tiles.get(f'{last + 1}-{row}'):
                last += 1

        elif direction == 'vertical':
            if not first:
                first = row
            if not last:
                last = row

            while self.tiles.get(f'{column}-{first - 1}'):
                first -= 1
            while self.tiles.get(f'{column}-{last + 1}'):
                last += 1

        if first == last:
            return

        for current in range(first, last + 1):
            coords = None
            if direction == 'horizontal':
                coords = f'{current}-{row}'
            elif direction == 'vertical':
                coords = f'{column}-{current}'

            tile = self.tiles.get(coords)
            if not tile:
                self.illegal_move()

            if not self.tiles_added_in_current_turn.get(coords):
                self.is_connected = True

            points = tile.points

            if self.tiles_added_in_current_turn.get(coords):
                if coords in self.double_letter_bonuses:
                    points *= 2
                elif coords in self.triple_letter_bonuses:
                    points *= 3
                elif coords in self.double_word_bonuses:
                    word_multiplier *= 2
                elif coords in self.triple_word_bonuses:
                    word_multiplier *= 3

            word_points += points
            word += tile.letter

        self.words.append(word)
        self.points += word_points * word_multiplier

    def end_turn(self):
        column = row = None
        columns = []
        rows = []
        self.is_connected = False

        if not self.tiles.get('7-7'):
            self.illegal_move()
            return

        if self.tiles_added_in_current_turn.get('7-7'):
            self.is_connected = True

        for coords in self.tiles_added_in_current_turn:
            x, y = split_coords(coords)
            if not column and not row:
                column, row = x, y
            elif column and row:
                if row == y:
                    column = rows = None
                elif column == x:
                    row = columns = None
                else:
                    self.illegal_move()
                    return
            if column:
                if column == x:
                    rows.append(y)
                else:
                    self.illegal_move()
                    return
            if row:
                if row == y:
                    columns.append(x)
                else:
                    self.illegal_move()
                    return

        self.words = []
        self.points = 0

        if rows:
            self.add_word_and_points(column, rows[0], 'vertical', min(rows), max(rows))

            for row in rows:
                self.add_word_and_points(column, row, 'horizontal')

        elif columns:
            self.add_word_and_points(columns[0], row, 'horizontal', min(columns), max(columns))

            for column in columns:
                self.add_word_and_points(column, row, 'vertical')

        if not self.is_connected:
            self.illegal_move()
            return

        for tile in self.tiles_added_in_current_turn.values():
            tile.set_immovable()

        print(self.words)
        print(self.points)

        self.add_letters_to_rack()
        # self.tiles_added_in_current_turn = {}

    def on_tile_move(self, tile):
        x, y = split_coords(tile.coords)

        if y == 15 or y == 16 and not 3 < x < 12:
            tile.undo_move()
            return
        elif other_tile := self.tiles.get(tile.coords):
            tile.swap_with_other(other_tile)

            self.tiles[tile.coords] = tile
            self.tiles[other_tile.coords] = other_tile

            if is_coords_of_rack(tile.coords):
                self.tiles_in_rack[tile.coords] = tile
            else:
                self.tiles_added_in_current_turn[tile.coords] = tile

            if is_coords_of_rack(other_tile.coords):
                self.tiles_in_rack[other_tile.coords] = other_tile
            else:
                self.tiles_added_in_current_turn[other_tile.coords] = other_tile

        else:
            if y != 16 and tile.old_coords.split('-')[1] == '16':
                self.rack.remove(tile.letter)
            del self.tiles[tile.old_coords]
            self.tiles[tile.coords] = tile

            if is_coords_of_rack(tile.coords):
                self.tiles_in_rack[tile.coords] = tile
            else:
                self.tiles_added_in_current_turn[tile.coords] = tile

            if is_coords_of_rack(tile.old_coords):
                del self.tiles_in_rack[tile.old_coords]
            else:
                del self.tiles_added_in_current_turn[tile.old_coords]

    def build_board_scene(self):
        self.build_squares()
        self.build_bonus_fields()
        self.build_rack()

    def build_squares(self):

        brush = QBrush(Qt.white)
        pen = QPen(Qt.black, 1, Qt.SolidLine)

        for row in range(self.rows):
            for column in range(self.columns):
                square = self.add_square(row, column, pen, brush)

                self.squares[f"{row}-{column}"] = square

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
            coords = f"{column}-16"
            if not self.tiles.get(coords) and len(self.tiles_in_rack) < 7:
                letter = self.sack.draw_one()
                self.rack.append(letter)

                position = QPointF(column * 40.0 + 30, 16 * 40.0 + 22)
                points = Sack.values.get(letter)
                tile = Tile(letter, points, position, self.on_tile_move)
                self.scene.addItem(tile)
                self.tiles_in_rack[coords] = tile
                self.tiles[coords] = tile

    def add_square(self, row, column, pen, brush):
        height = self.size * self.scale_manual
        width = self.size * self.scale_manual

        column_distance = column * width
        row_distance = row * height

        screen_offset = 2 * self.scale_manual

        x = column_distance + screen_offset
        y = row_distance + screen_offset

        rectangle = QRectF(x, y, width, height)

        return self.scene.addRect(rectangle, pen, brush)

    def create_bonus_fields(self):

        triple_word_brush = QBrush(QColor(255, 0, 0, 180))
        triple_word_bonuses = {
            "Name": "triple word",
            "Brush": triple_word_brush,
            "Positions": triple_word_bonus_coords
        }
        self.triple_word_bonuses = triple_word_bonus_coords
        self.bonus_fields.append(triple_word_bonuses)

        double_word_brush = QBrush(QColor(255, 0, 0, 100))

        double_word_bonuses = {
            "Name": "double word",
            "Brush": double_word_brush,
            "Positions": double_word_bonus_coords
        }
        self.double_word_bonuses = double_word_bonus_coords
        self.bonus_fields.append(double_word_bonuses)

        triple_letter_brush = QBrush(QColor(0, 0, 255, 180))

        triple_letter_bonuses = {
            "Name": "triple letter",
            "Brush": triple_letter_brush,
            "Positions": triple_letter_bonus_coords
        }
        self.triple_letter_bonuses = triple_letter_bonus_coords
        self.bonus_fields.append(triple_letter_bonuses)

        double_letter_brush = QBrush(QColor(0, 0, 255, 100))

        double_letter_bonuses = {
            "Name": "double letter",
            "Brush": double_letter_brush,
            "Positions": double_letter_bonus_coords
        }
        self.double_letter_bonuses = double_letter_bonus_coords
        self.bonus_fields.append(double_letter_bonuses)


class Algorithm:
    def __init__(self, board_to_play):
        self.board = board_to_play

        self.words = {}
        self.rack = self.board.sack.draw(7)
        self.tiles = None
        self.permutations = None

    def turn(self):
        self.tiles = self.board.tiles
        self.words = [set() for _ in range(16)]

        for tile in self.tiles.keys():
            if is_coords_of_rack(tile.coors):
                continue
            if not tile_above(tile, self.tiles):
                continue
            if not tile_on_right(tile, self.tiles):
                continue


# def app():
#     global app
#     app = QtWidgets.QApplication(sys.argv)


def main(frame):
    main_window = QMainWindow()

    main_window.setCentralWidget(frame)
    width = frame.width() + 10
    height = int(frame.height() * 1.6)

    main_window.setFixedSize(width, height)
    main_window.show()
    # main.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    board = Board()
    main(board)
