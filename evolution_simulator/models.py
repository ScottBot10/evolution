from enum import Enum
from math import sqrt, trunc
from .serializer.structures import Action, PosStruct


class Direction(Enum):  # uint3
    SW = 0
    S = 1
    SE = 2
    W = 3
    CENTER = 4
    E = 5
    NW = 6
    N = 7
    NE = 8

    def as_normalized_coord(self):
        d = self.value
        return Coord((d % 3) - 1, trunc(d / 3) - 1)

    def rotate(self, n=0):
        return rotations[self.value * 8 + (n & 7)]

    def rotate90CW(self):
        return self.rotate(2)

    def rotate90CCW(self):
        return self.rotate(-2)

    def rotate180(self):
        return self.rotate(4)

    @classmethod
    def random(cls, prng):
        return cls.N.rotate(prng.randint(0, 8))


SW, S, SE, W, C, E, NW, N, NE = Direction.SW, Direction.S, Direction.SE, Direction.W, Direction.CENTER, \
    Direction.E, Direction.NW, Direction.N, Direction.NE
rotations = (
    SW, W, NW, N, NE, E, SE, S,
    S, SW, W, NW, N, NE, E, SE,
    SE, S, SW, W, NW, N, NE, E,
    W, NW, N, NE, E, SE, S, SW,
    C, C, C, C, C, C, C, C,
    E, SE, S, SW, W, NW, N, NE,
    NW, N, NE, E, SE, S, SW, W,
    N, NE, E, SE, S, SW, W, NW,
    NE, E, SE, S, SW, W, NW, N
)

tanN = 13860
tanD = 33461
coord_to_dir = (S, C, SW, N, SE, E, N, N, N, N, W, NW, N, NE, N, N)


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def is_normalized(self):
        return -1 <= self.x <= 1 and -1 <= self.y <= 1

    def normalize(self):
        return self.as_dir().as_normalized_coord()

    def to_action(self):
        return Action(self.x, self.y)

    @classmethod
    def from_action(cls, action: Action):
        return cls(action.moveX, action.moveY)

    def to_pos_struct(self):
        return PosStruct(self.x, self.y)

    @classmethod
    def from_pos_struct(cls, pos_struct):
        return cls(pos_struct.x, pos_struct.y)

    def length(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def as_dir(self):
        xp = self.x * tanD + self.y * tanN
        yp = self.y * tanD - self.x * tanN
        return coord_to_dir[(yp > 0) * 8 + (xp > 0) * 4 + (yp > xp) * 2 + (yp >= -xp)]

    def ray_sameness(self, other):
        if isinstance(other, Direction):
            other = other.as_normalized_coord()
        if isinstance(other, Coord):
            mag = (self.x * self.x + self.y * self.y) * (other.x * other.x + other.y * other.y)
            if not mag:
                return 1
            return (self.x * other.x + self.y + other.y) / sqrt(mag)

    def visit_neighbourhood(self, grid_x: int, grid_y: int, radius: float, callback):
        for dx in range(int(-min(int(radius), self.x)), min(int(radius), (grid_x - self.x) - 1) + 1):
            x = self.x + dx
            extentY = int(sqrt(radius * radius - dx * dx))
            for dy in range(-min(extentY, self.y), min(extentY, (grid_y - self.y) - 1) + 1):
                y = self.y + dy
                callback(Coord(x, y))

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.x}, {self.y})"

    __str__ = __repr__

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y) if isinstance(other, Coord) else False

    def __add__(self, other):
        if isinstance(other, Direction):
            other = other.as_normalized_coord()
        if isinstance(other, Coord):
            return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if isinstance(other, Direction):
            other = other.as_normalized_coord()
        if isinstance(other, Coord):
            return Coord(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Coord(self.x * other, self.y * other)

    def __bool__(self):
        return bool(self.x or self.y)
