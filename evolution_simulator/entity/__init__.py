import typing as t

import numpy as np

from .entity_io import actions
from .genome import Gene, GeneContainer, Genome, NeuralNetwork
from ..models import Coord, Direction

if t.TYPE_CHECKING:
    from ..simulator import Simulator


class Entity:
    def __init__(self, index, loc: Coord, nn: NeuralNetwork, genome: Genome, prng, k):
        self.index = index
        self.loc = loc
        self.nn = nn
        self.genome = genome

        self.age = 0
        self.responsiveness = 0.5
        self.responsiveness_adjusted = self.response_curve(self.responsiveness, k)
        self.alive = True
        self.prev_dir: Direction = Direction.random(prng)
        self.challenge_data = None

    def move(self, offset: Coord, sim: 'Simulator'):
        loc = self.loc + offset
        if sim.is_empty(loc):
            self.prev_dir = offset.as_dir()
            sim[self.loc] = 0
            sim[loc] = self.index
            self.loc = loc
            sim.serializer.entity_move(self, sim, offset)

    def response_curve(self, r, k):
        return (r - 2) ** (-2 * k) - 2 ** (-2 * k) * (1 - r)

    def execute_actions(self, sim, action_levels):
        groups = {}
        for i, action_level in action_levels.items():
            action = actions[i]
            if action.group is None:
                action.execute(self, sim, action_level)
            else:
                if action.group not in groups:
                    group = action.group(self, sim)
                    groups[action.group] = group
                else:
                    group = groups[action.group]
                group.execute(action, self, sim, action_level)
        for group in groups.values():
            group.execute_all(self, sim)


def init_entities(prng, grid, entity_count, genome_length, max_hidden_neurons, k) -> t.List[Entity]:
    grid_shape = m, n = grid.shape
    entities = []
    for i, val in enumerate(prng.choice(m * n, entity_count, False), start=1):
        loc = np.unravel_index(val, grid_shape)
        grid[loc] = i
        genome = [GeneContainer.random(prng) for _ in range(genome_length)]
        entities.append(Entity(i, Coord(*loc), NeuralNetwork.from_genome(genome, max_hidden_neurons), genome, prng, k))
    return entities
