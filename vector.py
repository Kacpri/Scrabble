from typing import List


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
        return f'({self._x}, {self._y})'

    def __neg__(self):
        return Vector(-self._x, -self._y)

    def __abs__(self):
        return Vector(abs(self._x), abs(self._y))

    def __add__(self, other):
        return Vector(self._x + other.x, self._y + other.y)

    def __sub__(self, other):
        return Vector(self._x - other.x, self._y - other.y)

    def __mul__(self, other):
        return Vector(self._x * other, self._y * other)

    def __rmul__(self, other):
        return Vector(self._x * other, self._y * other)
