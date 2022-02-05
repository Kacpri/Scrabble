from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPen, QBrush, QFont, QFontMetrics
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsSimpleTextItem

from coords import Coords
from dictionary import BLANK
from constants import SQUARE_SIZE, MARGIN
from colors import *


class Tile(QGraphicsRectItem):
    def __init__(self, letter, points, coords, scale, on_position_change=None, move_to_rack=None, parent=None):
        QGraphicsRectItem.__init__(self, MARGIN, MARGIN, SQUARE_SIZE - 2 * MARGIN, SQUARE_SIZE - 2 * MARGIN, parent)
        if on_position_change:
            self.on_position_change = on_position_change
        if move_to_rack:
            self.move_to_rack = move_to_rack

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.points = points
        self.letter = letter

        self.scale = scale
        self.setScale(self.scale)
        self.setZValue(3)

        self.setPen(QPen(YELLOW2, 0))
        self.setBrush(QBrush(YELLOW))

        self.letter_item = QGraphicsSimpleTextItem(letter, self)

        self.font = QFont("Verdana", 20)
        if not points:
            self.font.setItalic(True)
        font_metrics = QFontMetrics(self.font)
        height = font_metrics.height()
        width = font_metrics.width(self.letter)

        self.letter_item.setX((SQUARE_SIZE - width) / 2 - MARGIN)
        self.letter_item.setY((SQUARE_SIZE - height) / 2 - MARGIN)
        self.letter_item.setFont(self.font)
        self.letter_item.setBrush(QBrush(SEA_GREEN))

        self.shadow = QGraphicsRectItem(MARGIN * 2, MARGIN * 2, SQUARE_SIZE, SQUARE_SIZE, self)
        self.shadow.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.shadow.setBrush(QBrush(TRANSPARENT_BLACK))
        self.shadow.setPen(QPen(TRANSPARENT, 0))
        self.shadow.hide()

        self.setPos(coords.x * SQUARE_SIZE * scale, coords.y * SQUARE_SIZE * scale)
        self.coords = None
        self.update_coords()

        self.old_position = None
        self.old_coords = None

        self.is_placed = False

        if points:
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

    def change_to_blank(self, new_letter):
        if self.letter == BLANK:
            self.letter = new_letter.upper()
            self.letter_item.setText(new_letter)
            self.font.setItalic(True)
            font_metrics = QFontMetrics(self.font)
            height = font_metrics.height()
            width = font_metrics.width(self.letter)
            self.letter_item.setFont(self.font)
            self.letter_item.setX((SQUARE_SIZE - width) / 2 - MARGIN)
            self.letter_item.setY((SQUARE_SIZE - height) / 2 - MARGIN)

    def change_back(self):
        self.letter = BLANK
        self.letter_item.setText(BLANK)

    def get_letter_and_points(self):
        return self.letter, self.points

    def mousePressEvent(self, event):
        if self.is_placed:
            return
        if event.button() == Qt.RightButton:
            return
        self.setScale(self.scale * 1.1)

        self.setZValue(10)
        self.old_position = self.pos()
        self.old_coords = self.coords

        self.setPos(self.x() - 2 * MARGIN, self.y() - 2 * MARGIN)
        self.shadow.show()
        QGraphicsRectItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.is_placed:
            return
        if event.button() == Qt.RightButton:
            self.move_to_rack(self)
            return
        self.setScale(self.scale)

        current_position = self.pos()
        self.setX(round((self.x() + MARGIN * 2) / (SQUARE_SIZE * self.scale)) * SQUARE_SIZE * self.scale)
        self.setY(round((self.y() + MARGIN * 2) / (SQUARE_SIZE * self.scale)) * SQUARE_SIZE * self.scale)

        if current_position != self.pos():
            self.update_coords()
            self.on_position_change(self)

        self.setZValue(3)
        self.shadow.hide()
        QGraphicsRectItem.mouseReleaseEvent(self, event)

    def update_coords(self):
        x = round(self.x() / SQUARE_SIZE / self.scale)
        y = round(self.y() / SQUARE_SIZE / self.scale)
        self.coords = Coords(x, y)

    def move(self, position):
        self.setPos(position)
        self.update_coords()

    def move_to_coords(self, coords):
        position = QPoint(coords.x * SQUARE_SIZE * self.scale, coords.y * SQUARE_SIZE * self.scale)
        self.move(position)

    def undo_move(self):
        self.setPos(self.old_position)
        self.update_coords()

    def swap_with_other(self, other):
        other.move(self.old_position)

    def remove_highlight(self):
        self.letter_item.setBrush(QBrush(SEA_GREEN))

    def place(self, highlight=False):
        if highlight:
            self.letter_item.setBrush(QBrush(LIGHT_SEA_GREEN))
        self.setBrush(QBrush(YELLOW2))
        self.setPen(QPen(YELLOW2, 0))
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.is_placed = True
