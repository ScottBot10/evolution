import typing as t
from math import sqrt, pi, ceil

from .vectors import Vector, VectorGroup

if t.TYPE_CHECKING:
    from .simulator import Simulator
    from .entity import Entity

selection_pressures = VectorGroup()

SurvivalScores = t.Dict[int, float]


class SelectionPressure(Vector):
    vector_group = selection_pressures

    def __init__(self, parameters, *data, from_serialize=False):
        self.from_serialize = from_serialize

    def to_data(self):
        return 0

    @classmethod
    def from_data(cls, parameters, data):
        return cls(parameters, from_serialize=True)

    def select_entity(self, entity: 'Entity') -> float | None:
        pass

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        return {
            entity.index: score
            for entity in simulator.entities
            if (score := self.select_entity(entity)) is not None
        }

    on_step = None


class AllSurvive(SelectionPressure):
    enabled = True
    id = 0

    def select_entity(self, entity: 'Entity') -> float | None:
        return 1


class LeftHalf(SelectionPressure):
    enabled = True
    id = 1

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            self.half_pos = parameters.World.grid_x / 2
        else:
            self.half_pos = parameters.grid.x / 2

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.x <= self.half_pos:
            return 1 - (entity.loc.x / self.half_pos)


class LeftQuarter(SelectionPressure):
    enabled = True
    id = 2

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            self.quarter_pos = parameters.World.grid_x / 4
        else:
            self.quarter_pos = parameters.grid.x / 4

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.x <= self.quarter_pos:
            return 1 - (entity.loc.x / self.quarter_pos)


class RightHalf(SelectionPressure):
    enabled = True
    id = 3

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            self.half_pos = parameters.World.grid_x / 2
        else:
            self.half_pos = parameters.grid.x / 2

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.x >= self.half_pos:
            return (entity.loc.x / self.half_pos) - 1


class RightQuarter(SelectionPressure):
    enabled = True
    id = 4

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            x = parameters.World.grid_x
        else:
            x = parameters.grid.x
        self.quarter_pos = x / 4
        self.right_quarter_pos = x * 3 / 4

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.x >= self.right_quarter_pos:
            return (entity.loc.x / self.quarter_pos) - 3


class TopHalf(SelectionPressure):
    enabled = True
    id = 5

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            self.half_pos = parameters.World.grid_y / 2
        else:
            self.half_pos = parameters.grid.y / 2

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.y >= self.half_pos:
            return 1 - (entity.loc.y / self.half_pos)


class BottomHalf(SelectionPressure):
    enabled = True
    id = 6

    def __init__(self, parameters, *data, from_serialize=False):
        super().__init__(parameters, *data, from_serialize=from_serialize)
        if not self.from_serialize:
            self.half_pos = parameters.World.grid_y / 2
        else:
            self.half_pos = parameters.grid.y / 2

    def select_entity(self, entity: 'Entity') -> float | None:
        if entity.loc.y <= self.half_pos:
            return (entity.loc.y / self.half_pos) - 1


class Circle(SelectionPressure):
    enabled = True
    id = 7

    def __init__(self, parameters, radius=None, percent_of_entities=1, from_serialize=False):
        super().__init__(parameters, from_serialize=from_serialize)
        if not self.from_serialize:
            self.half_x = parameters.World.grid_x / 2
            self.half_y = parameters.World.grid_y / 2
            if not radius:
                entity_count = parameters.World.entity_count * percent_of_entities
                self.radius = min(self.half_x, self.half_y, ceil(sqrt(entity_count / pi)))
            else:
                self.radius = radius
        else:
            self.radius = radius

    def to_data(self):
        return self.radius

    @classmethod
    def from_data(cls, simulator, data):
        return cls(simulator, radius=data, from_serialize=True)

    def select_entity(self, entity: 'Entity') -> float | None:
        distance = sqrt((entity.loc.x - self.half_x) ** 2 + (entity.loc.y - self.half_y) ** 2)
        if distance <= self.radius:
            return 1 - (distance / self.radius)
