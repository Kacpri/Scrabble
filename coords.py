from typing import List, Set

from constants import EXCHANGE_ROW, RACK_ROW, LEFT_RACK_BOUND, RIGHT_RACK_BOUND, FIRST_COLUMN, FIRST_ROW, LAST_COLUMN, \
    LAST_ROW, CENTER
from vector import Vector


class Coords:
    @classmethod
    def central(cls) -> 'Coords':
        return cls(CENTER, CENTER)

    @classmethod
    def from_notation(cls, notation: str) -> 'Coords':
        x = ord(notation[0]) - ord('A')
        y = int(notation[1:]) - 1
        return cls(x, y)

    @classmethod
    def algebraic_notations_to_coords(cls, algebraic_notations: List[str]) -> Set['Coords']:
        return set(map(cls.from_notation, algebraic_notations))

    def __init__(self, x: int, y: int) -> None:
        if not isinstance(y, int) or not isinstance(x, int):
            raise ValueError('Coords must contain integers')
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def __str__(self) -> str:
        x = chr(ord('A') + self.x)
        return f'{x}{self.y + 1}'

    def __hash__(self):
        return hash(self.x * 15 + self.y)

    def __lt__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        if self.x > other.x or self.y > other.y:
            return False
        return self.x < other.x or self.y < other.y

    def __le__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        if self.x > other.x or self.y > other.y:
            return False
        return self.x <= other.x or self.y <= other.y

    def __gt__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        if self.x < other.x or self.y < other.y:
            return False
        return self.x > other.x or self.y > other.y

    def __ge__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        if self.x < other.x or self.y < other.y:
            return False
        return self.x >= other.x or self.y >= other.y

    def __eq__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __ne__(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        return self.x != other.x or self.y != other.y

    def copy(self) -> 'Coords':
        return Coords(self.x, self.y)

    def move(self, vector: Vector) -> 'Coords':
        if not isinstance(vector, Vector):
            raise ValueError('You must provide valid vector')
        return Coords(self.x + vector.x, self.y + vector.y)

    def is_same_row(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        return self.y == other.y

    def is_same_column(self, other: 'Coords') -> bool:
        if not isinstance(other, Coords):
            return NotImplemented
        return self.x == other.x

    def distance_to(self, other: 'Coords') -> int:
        if not isinstance(other, Coords):
            return NotImplemented
        if self.is_same_row(other):
            return abs(self.y - other.y)
        elif self.is_same_column(other):
            return abs(self.x - other.x)
        return -1

    def is_in_rack(self) -> bool:
        return self.y == RACK_ROW and LEFT_RACK_BOUND <= self.x <= RIGHT_RACK_BOUND

    def is_in_exchange_zone(self) -> bool:
        return self.y == EXCHANGE_ROW and LEFT_RACK_BOUND <= self.x <= RIGHT_RACK_BOUND

    def is_on_board(self) -> bool:
        return FIRST_COLUMN <= self.x <= LAST_COLUMN and FIRST_ROW <= self.y <= LAST_ROW

    def is_valid(self) -> bool:
        return self.is_in_rack() or self.is_in_exchange_zone() or self.is_on_board()
