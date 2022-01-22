from coords import Coords
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

    def get_functions(self):
        if self == Direction.UP:
            return Coords.above, Coords.below
        elif self == Direction.DOWN:
            return Coords.below, Coords.above
        elif self == Direction.LEFT:
            return Coords.on_left, Coords.on_right
        elif self == Direction.RIGHT:
            return Coords.on_right, Coords.on_left
