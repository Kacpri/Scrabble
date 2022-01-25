from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from coords import Coords
from dictionary import BLANK
from constants import SQUARE_SIZE, MARGIN
from colors import YELLOW, YELLOW2, SEA_GREEN


class Tile(QGraphicsRectItem):
    DARK_BROWN = QColor(165, 131, 85, 255)
    BROWN = QColor(193, 157, 109, 255)
    LIGHT_BROWN = QColor(222, 184, 135, 255)

    def __init__(self, letter, points, coords, scale, on_position_change=None, parent=None):
        QGraphicsRectItem.__init__(self, MARGIN, MARGIN, SQUARE_SIZE - 2 * MARGIN, SQUARE_SIZE - 2 * MARGIN, parent)
        if on_position_change:
            self.on_position_change = on_position_change

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.points = points
        self.letter = letter

        self.scale = scale
        self.setScale(scale)
        self.setZValue(3)
        self.move_restrict_rect = QRectF(0, 0, SQUARE_SIZE * 15 * scale, SQUARE_SIZE * 18 * scale)

        self.setPen(QPen(YELLOW, 0))
        self.setBrush(QBrush(YELLOW))

        self.letter_item = QGraphicsSimpleTextItem(letter, self)
        self.font = QFont("Verdana", 20)
        font_metrics = QFontMetrics(self.font)
        height = font_metrics.height()
        width = font_metrics.width(self.letter)

        self.letter_item.setX((SQUARE_SIZE - width) / 2 - MARGIN)
        self.letter_item.setY((SQUARE_SIZE - height) / 2 - MARGIN)
        self.letter_item.setFont(self.font)
        self.letter_item.setBrush(QBrush(SEA_GREEN))

        self.setPos(coords.x * SQUARE_SIZE * scale, coords.y * SQUARE_SIZE * scale)
        self.coords = None
        self.update_coords()

        self.old_position = None
        self.old_coords = None

        self.is_placed = False

        if letter != BLANK:
            points = QGraphicsSimpleTextItem(str(self.points), self)
            font = QFont("Verdana", 10)
            font_metrics = QFontMetrics(font)
            height = font_metrics.height()
            width = font_metrics.width(str(self.points))
            points.setFont(font)
            points.setBrush(QBrush(SEA_GREEN))
            points.setX(SQUARE_SIZE - MARGIN - width)
            points.setY(SQUARE_SIZE - MARGIN - height)

    def __str__(self):
        return self.letter

    def resize(self, scale):
        self.scale = scale
        self.setScale(scale)
        self.setPos(self.coords.x * SQUARE_SIZE * scale, self.coords.y * SQUARE_SIZE * scale)
        self.move_restrict_rect = QRectF(0, 0, SQUARE_SIZE * 15 * scale, SQUARE_SIZE * 18 * scale)

    def change_blank(self, new_letter):
        if self.letter == BLANK:
            self.letter = new_letter.upper()
            self.letter_item.setText(new_letter)

    def change_back(self):
        self.letter = BLANK
        self.letter_item.setText(BLANK)

    def get_letter_and_points(self):
        return self.letter, self.points

    def mousePressEvent(self, event):
        self.setZValue(4)
        self.old_position = self.pos()
        self.old_coords = self.coords
        QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.move_restrict_rect.contains(event.scenePos()):
            QGraphicsRectItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        current_position = self.pos()

        self.setX(round(self.x() / (SQUARE_SIZE * self.scale)) * SQUARE_SIZE * self.scale)
        self.setY(round(self.y() / (SQUARE_SIZE * self.scale)) * SQUARE_SIZE * self.scale)

        self.update_coords()

        if current_position.x is not self.x() or current_position.y is not self.y():
            self.on_position_change(self)

        self.setZValue(3)
        QGraphicsRectItem.mouseReleaseEvent(self, event)

    def update_coords(self):
        x = round(self.x() / SQUARE_SIZE / self.scale)
        y = round(self.y() / SQUARE_SIZE / self.scale)
        self.coords = Coords(x, y)

    def move(self, position):
        self.setPos(position)
        self.update_coords()

    def undo_move(self):
        self.setPos(self.old_position)
        self.update_coords()

    def swap_with_other(self, other):
        other.move(self.old_position)

    def place(self):
        self.setBrush(QBrush(YELLOW2))
        self.setPen(QPen(YELLOW2, 0))
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.is_placed = True
