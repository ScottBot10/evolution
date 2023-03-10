import typing as t

from .vectors import Vector, VectorGroup

if t.TYPE_CHECKING:
    from .simulator import Simulator

selection_pressures = VectorGroup()

SurvivalScores = t.Dict[int, float]


class SelectionPressure(Vector):
    vector_group = selection_pressures

    def __init__(self, simulator: 'Simulator'):
        pass

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        pass

    on_step = None


class AllSurvive(SelectionPressure):
    enabled = True

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        return {entity.index: 1 for entity in simulator.entities}


class LeftHalf(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.half_pos = simulator.Parameters.World.grid_x / 2

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.x <= self.half_pos:
                survival_scores[entity.index] = 1 - (entity.loc.x / self.half_pos)
        return survival_scores


class LeftQuarter(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.quarter_pos = simulator.Parameters.World.grid_x / 4

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.x <= self.quarter_pos:
                survival_scores[entity.index] = 1 - (entity.loc.x / self.quarter_pos)
        return survival_scores


class RightHalf(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.half_pos = simulator.Parameters.World.grid_x / 2

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.x >= self.half_pos:
                survival_scores[entity.index] = (entity.loc.x / self.half_pos) - 1
        return survival_scores


class RightQuarter(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.quarter_pos = simulator.Parameters.World.grid_x / 4
        self.right_quarter_pos = simulator.Parameters.World.grid_x * 3 / 4

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.x >= self.right_quarter_pos:
                survival_scores[entity.index] = (entity.loc.x / self.quarter_pos) - 3
        return survival_scores


class TopHalf(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.half_pos = simulator.Parameters.World.grid_y / 2

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.y >= self.half_pos:
                survival_scores[entity.index] = 1 - (entity.loc.y / self.half_pos)
        return survival_scores


class BottomHalf(SelectionPressure):
    enabled = True

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self.half_pos = simulator.Parameters.World.grid_y / 2

    def select(self, simulator: 'Simulator') -> SurvivalScores:
        survival_scores = {}

        for entity in simulator.entities:
            if entity.loc.y <= self.half_pos:
                survival_scores[entity.index] = (entity.loc.y / self.half_pos) - 1
        return survival_scores
