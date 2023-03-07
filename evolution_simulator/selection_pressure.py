import typing as t

from .vectors import Vector, VectorGroup

if t.TYPE_CHECKING:
    from .simulator import Simulator

selection_pressures = VectorGroup()

SurvivalScores = t.Dict[int, float]


class SelectionPressure(Vector):
    vector_group = selection_pressures

    @classmethod
    def select(cls, simulator: 'Simulator') -> SurvivalScores:
        pass

    on_step = None


class AllSurvive(SelectionPressure):
    enabled = True

    @classmethod
    def select(cls, simulator: 'Simulator') -> SurvivalScores:
        return {entity.index: 1 for entity in simulator.entities}


class RightHalf(SelectionPressure):
    enabled = True

    @classmethod
    def select(cls, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}
        half_pos = simulator.Parameters.World.grid_x / 2
        for entity in simulator.entities:
            if entity.loc.x < half_pos:
                survival_scores[entity.index] = 1 - ((half_pos - entity.loc.x) / half_pos)
        return survival_scores
