from math import tanh

from .base import VectorGroup, EntityVector, Group
from ...models import Direction, Coord

actions = VectorGroup()


def prob_to_bool(prng, prob):
    return prng.random() < prob


class MovementGroup(Group):
    def __init__(self, entity, sim):
        self.moveX = 0
        self.moveY = 0
        self.last_move_offset = entity.prev_dir.as_normalized_coord()

    def execute_all(self, entity, sim):
        self.moveX = tanh(self.moveX) * entity.responsiveness_adjusted
        self.moveY = tanh(self.moveY) * entity.responsiveness_adjusted

        prob_x = int(prob_to_bool(sim.prng, abs(self.moveX)))
        prob_y = int(prob_to_bool(sim.prng, abs(self.moveY)))

        sign_x = -1 if self.moveX < 0 else 1
        sign_y = -1 if self.moveY < 0 else 1

        offset = Coord(prob_x * sign_x, prob_y * sign_y)
        if offset:
            entity.move(offset, sim)


class ActionBase(EntityVector):
    vector_group = actions

    @classmethod
    def execute(cls, entity, sim, level):
        pass


class MovementBase(ActionBase):
    group = MovementGroup

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        pass


class SetResponsiveness(ActionBase):
    enabled = True
    name = 'set responsiveness'
    short_name = 'Res'

    @classmethod
    def execute(cls, entity, sim, level):
        level = (tanh(level) + 1) / 2
        entity.responsiveness = level
        entity.responsiveness_adjusted = entity.response_curve(level,
                                                               sim.Parameters.Entities.responsiveness_curve_kfactor)


class MoveX(MovementBase):
    enabled = True
    name = 'move X'
    short_name = 'MvX'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveX += level


class MoveY(MovementBase):
    enabled = True
    name = 'move Y'
    short_name = 'MvY'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveY += level


class MoveForward(MovementBase):
    enabled = True
    name = 'move forward'
    short_name = 'MFw'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveX += group.last_move_offset.x * level
        group.moveY += group.last_move_offset.y * level


class MoveBackward(MovementBase):
    enabled = True
    name = 'move backward'
    short_name = 'MBk'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveX -= group.last_move_offset.x * level
        group.moveY -= group.last_move_offset.y * level


class MoveRandom(MovementBase):
    enabled = True
    name = 'move random'
    short_name = 'MRnd'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        offset = Direction.random(sim.prng).as_normalized_coord()
        group.moveX += offset.x * level
        group.moveY += offset.y * level


class MoveEast(MovementBase):
    enabled = True
    name = 'move east'
    short_name = 'MvE'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveX += level


class MoveWest(MovementBase):
    enabled = True
    name = 'move west'
    short_name = 'MvW'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveX -= level


class MoveNorth(MovementBase):
    enabled = True
    name = 'move north'
    short_name = 'MvN'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveY += level


class MoveSouth(MovementBase):
    enabled = True
    name = 'move south'
    short_name = 'MvS'

    @classmethod
    def execute_group(cls, entity, sim, level: float, group: MovementGroup):
        group.moveY -= level


class Kill(ActionBase):
    enabled = False
    name = 'kill'
    short_name = 'Kill'


assert actions.check()
