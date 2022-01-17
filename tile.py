from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from coords import Coords
from dictionary import BLANK

SQUARE_SIZE = 40
MARGIN = 2


class Tile(QGraphicsRectItem):
    def __init__(self, letter, points, coords, on_position_change=None, parent=None):
        QGraphicsRectItem.__init__(self, MARGIN, MARGIN, SQUARE_SIZE - 2 * MARGIN, SQUARE_SIZE - 2 * MARGIN, parent)
        if on_position_change:
            self.on_position_change = on_position_change

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.points = points
        self.letter = letter

        self.setZValue(3)
        self.move_restrict_rect = QRectF(SQUARE_SIZE / 2, SQUARE_SIZE / 2, SQUARE_SIZE * 14,
                                         SQUARE_SIZE * 17)

        self.setPen(QPen(QColor(193, 157, 109, 255)))
        self.setBrush(QBrush(QColor(222, 184, 135, 255)))

        self.letter_item = QGraphicsSimpleTextItem(letter, self)
        font = QFont("Helvetica", 20)
        font_metrics = QFontMetrics(font)
        height = font_metrics.height()
        width = font_metrics.width(self.letter)
        self.letter_item.setX((SQUARE_SIZE - width) / 2 - MARGIN)
        self.letter_item.setY((SQUARE_SIZE - height) / 2 - MARGIN)
        self.letter_item.setFont(font)

        self.setPos(QPointF(coords.x() * SQUARE_SIZE, coords.y() * SQUARE_SIZE))
        self.coords = None
        self.update_coords()

        self.old_position = None
        self.old_coords = None

        # self.setFont(QtGui.QFont())
        points = QGraphicsSimpleTextItem(str(self.points), self)
        font = QFont("Helvetica", 10)
        font_metrics = QFontMetrics(font)
        height = font_metrics.height()
        width = font_metrics.width(str(self.points))
        points.setFont(font)
        points.setX(SQUARE_SIZE - MARGIN - width)
        points.setY(SQUARE_SIZE - MARGIN - height)

    def __str__(self):
        return self.letter

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
        self.old_position = self.pos()
        self.old_coords = self.coords
        QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.move_restrict_rect.contains(event.scenePos()):
            QGraphicsRectItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        current_position = self.pos()

        self.setX(round(self.x() / SQUARE_SIZE) * SQUARE_SIZE)
        self.setY(round(self.y() / SQUARE_SIZE) * SQUARE_SIZE)

        self.update_coords()

        if current_position.x() is not self.x() or current_position.y() is not self.y():
            self.on_position_change(self)
        QGraphicsRectItem.mouseReleaseEvent(self, event)

    def update_coords(self):
        x = int((self.x()) / SQUARE_SIZE)
        y = int((self.y()) / SQUARE_SIZE)
        self.coords = Coords(x, y)

    def move(self, position):
        self.setPos(position)
        self.update_coords()

    def undo_move(self):
        self.setPos(self.old_position)
        self.update_coords()

    def swap_with_other(self, other):
        other.move(self.old_position)

    def set_immovable(self):
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
