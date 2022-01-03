class Coords:
    @classmethod
    def from_notation(cls, notation):
        x = ord(notation[0]) - ord('A') + 1
        y = int(notation[1:])
        return Coords(x, y)

    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __str__(self):
        x = chr(ord('A') + self._x - 1)
        return f'{x}{self._y}'

    def __hash__(self):
        return hash(self._x * 15 + self._y - 1)

    def __lt__(self, other):
        if self._x > other.x() or self._y > other.y():
            return False
        return self._x < other.x() or self._y < other.y()

    def __le__(self, other):
        if self._x > other.x() or self._y > other.y():
            return False
        return self._x <= other.x() or self._y <= other.y()

    def __gt__(self, other):
        if self._x < other.x() or self._y < other.y():
            return False
        return self._x > other.x() or self._y > other.y()

    def __ge__(self, other):
        if self._x < other.x() or self._y < other.y():
            return False
        return self._x >= other.x() or self._y >= other.y()

    def __eq__(self, other):
        return self._x == other.x() and self._y == other.y()

    def __ne__(self, other):
        return self._x != other.x() or self._y != other.y()

    def x(self):
        return self._x

    def y(self):
        return self._y

    def get(self):
        return self._x, self._y

    def to_notation(self):
        letter = chr(ord('A') + self._x)
        number = str(self._y + 1)
        return letter + number

    def above(self):
        return Coords(self._x, self._y - 1)

    def below(self):
        return Coords(self._x, self._y + 1)

    def on_left(self):
        return Coords(self._x - 1, self._y)

    def on_right(self):
        return Coords(self._x + 1, self._y)

    def is_in_rack(self):
        return self._y == 16

    def is_same_row(self, coords):
        return self._y == coords.y()

    def is_same_column(self, coords):
        return self._x == coords.x()

    def is_valid(self):
        return self.is_in_rack() or (0 <= self._x < 15 and 0 <= self._y < 15)
