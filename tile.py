from PyQt5 import QtCore, QtWidgets
from coords import Coords


class Tile(QtWidgets.QGraphicsSimpleTextItem):
    def __init__(self, letter, points, position, on_position_change, parent=None):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, parent)
        self.on_position_change = on_position_change

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.points = points
        self.letter = letter

        self.offset_top = 22
        self.offset_right = 30
        self.square_size = 40

        self.move_restrict_rect = QtCore.QRectF(30, 30, 570, 660)

        self.setText(letter)
        self.setScale(2.5)
        self.setPos(position)

        self.coords = None
        self.update_coords()

        self.old_position = None
        self.old_coords = None

        # self.setFont(QtGui.QFont())
        points = QtWidgets.QGraphicsSimpleTextItem(str(self.points), self)
        points.setScale(0.5)
        points.setX(8)
        points.setY(8)

    def __str__(self):
        return self.letter

    def change_blank(self, new_letter):
        if self.letter == '_':
            self.letter = new_letter.upper()
            self.setText(new_letter)

    def mousePressEvent(self, event):
        self.old_position = self.pos()
        self.old_coords = self.coords
        QtWidgets.QGraphicsSimpleTextItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.move_restrict_rect.contains(event.scenePos()):
            QtWidgets.QGraphicsSimpleTextItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        current_position = self.pos()

        self.setX(round((self.x() - self.offset_right) / self.square_size) * self.square_size + self.offset_right)
        self.setY(round((self.y() - self.offset_top) / self.square_size) * self.square_size + self.offset_top)

        self.update_coords()

        if current_position.x() is not self.x() or current_position.y() is not self.y():
            self.on_position_change(self)
        QtWidgets.QGraphicsSimpleTextItem.mouseReleaseEvent(self, event)

    def update_coords(self):
        x = int((self.x() - self.offset_right) / self.square_size)
        y = int((self.y() - self.offset_top) / self.square_size)
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
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
