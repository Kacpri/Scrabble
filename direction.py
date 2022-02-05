from enum import Enum


class Direction(Enum):
    UP = 1
    DOWN = -1
    LEFT = 2
    RIGHT = -2

    def opposite(self):
        return Direction(-self.value)

    def perpendicular(self):
        return Direction(self.value % 2 + 1)

    def bivalent(self):
        return Direction(self.value % 2 - 2)
