class Vector:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __str__(self):
        if (self.x, self.y) == (1, 0):
            return 'RIGHT'
        if (self.x, self.y) == (-1, 0):
            return 'LEFT'
        if (self.x, self.y) == (0, 1):
            return 'DOWN'
        if (self.x, self.y) == (0, -1):
            return 'UP'
        return f'({self.x}, {self.y})'

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __invert__(self):
        return Vector(self.y, self.x)

    def __hash__(self):
        return hash(self.x) ^ hash(self.y)

    def __eq__(self, other):
        return other and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def __gt__(self, other):
        if self.x < other.x or self.y < other.y:
            return False
        return self.x > other.x or self.y > other.y

    def __lt__(self, other):
        if self.x > other.x or self.y > other.y:
            return False
        return self.x < other.x or self.y < other.y

    def __abs__(self):
        return Vector(abs(self.x), abs(self.y))

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __rmul__(self, other):
        return Vector(self.x * other, self.y * other)
