from math import sqrt

from .base import VectorGroup, EntityVector
from ..genome_difference import jaro_winkler, hamming_bits, hamming_bytes

sensors = VectorGroup()


class SensorBase(EntityVector):
    vector_group = sensors

    @classmethod
    def execute(cls, entity, simulator):
        return 0.5


def population_along_axis(location, direction, sim):
    pop_sum = [0]

    direction = direction.as_normalized_coord()
    length = sqrt(direction.x * direction.x + direction.y * direction.y)
    vec_x = direction.x / length
    vec_y = direction.y / length

    def callback(tloc):
        if tloc != location and sim.entity_at_pos(tloc):
            offset = tloc - location
            proj = vec_x * offset.x + vec_y * offset.y
            pop_sum[0] += proj / (offset.x * offset.x + offset.y * offset.y)

    location.visit_neighbourhood(sim.Parameters.World.grid_x, sim.Parameters.World.grid_y,
                                 sim.Parameters.Simulation.population_sensor_radius, callback)
    return ((pop_sum[0] / (6 * sim.Parameters.Simulation.population_sensor_radius)) + 1) / 2


class LocX(SensorBase):
    enabled = True
    name = 'loc X'
    short_name = 'Lx'

    @classmethod
    def execute(cls, entity, simulator):
        return entity.loc.x / (simulator.Parameters.World.grid_x - 1)


class LocY(SensorBase):
    enabled = True
    name = 'loc Y'
    short_name = 'Ly'

    @classmethod
    def execute(cls, entity, simulator):
        return entity.loc.y / (simulator.Parameters.World.grid_y - 1)


class BoundaryDistX(SensorBase):
    enabled = True
    name = 'boundary dist X'
    short_name = 'EDx'

    @classmethod
    def execute(cls, entity, simulator):
        min_x = min(entity.loc.x, (simulator.Parameters.World.grid_x - entity.loc.x) - 1)
        return min_x / (simulator.Parameters.World.grid_x / 2)


class BoundaryDist(SensorBase):
    enabled = True
    id = 4
    name = 'boundary dist'
    short_name = 'EDx'

    @classmethod
    def execute(cls, entity, simulator):
        min_x = min(entity.loc.x, (simulator.Parameters.World.grid_x - entity.loc.x) - 1)
        min_y = min(entity.loc.y, (simulator.Parameters.World.grid_y - entity.loc.y) - 1)
        closest = min(min_x, min_y)
        max_possible = max(simulator.Parameters.World.grid_x / 2 - 1, simulator.Parameters.World.grid_y / 2 - 1)
        return closest / max_possible


class BoundaryDistY(SensorBase):
    enabled = True
    id = 3
    name = 'boundary dist Y'
    short_name = 'EDy'

    @classmethod
    def execute(cls, entity, simulator):
        min_y = min(entity.loc.y, (simulator.Parameters.World.grid_y - entity.loc.y) - 1)
        return min_y / (simulator.Parameters.World.grid_y / 2)


class GeneticSimilarityForward(SensorBase):
    enabled = True
    name = 'genetic similarity fwd'
    short_name = 'Gen'

    @classmethod
    def execute(cls, entity, simulator):
        fwd = entity.loc + entity.prev_dir
        if simulator.loc_in_bounds(fwd) and simulator.entity_at_pos(fwd):
            other = simulator.entities[simulator[fwd] - 1]
            if other.alive:
                if simulator.Parameters.Entities.genetic_difference_algorithm == 0:
                    return jaro_winkler(entity.genome, other.genome)
                elif simulator.Parameters.Entities.genetic_difference_algorithm == 1:
                    return hamming_bits(entity.genome, other.genome)
                elif simulator.Parameters.Entities.genetic_difference_algorithm == 2:
                    return hamming_bytes(entity.genome, other.genome)
                else:
                    raise
        return 0


class LastMoveX(SensorBase):
    enabled = True
    name = 'last move X'
    short_name = 'LMx'

    @classmethod
    def execute(cls, entity, simulator):
        lastX = entity.prev_dir.as_normalized_coord().x
        return 0.5 if lastX == 0 else (0 if lastX == -1 else 1)


class LastMoveY(SensorBase):
    enabled = True
    name = 'last move Y'
    short_name = 'LMy'

    @classmethod
    def execute(cls, entity, simulator):
        lastY = entity.prev_dir.as_normalized_coord().y
        return 0.5 if lastY == 0 else (0 if lastY == -1 else 1)


class ProbePopulationFwd(SensorBase):
    enabled = True
    name = 'probe population forward'
    short_name = 'LPf'

    @classmethod
    def execute(cls, entity, simulator):
        long_probe_distance = simulator.Parameters.Simulation.long_probe_distance
        loc = entity.loc
        direction = entity.prev_dir

        for count in range(long_probe_distance):
            loc += direction
            if not simulator.loc_in_bounds(loc):
                return 1
            if simulator.entity_at_pos(loc):
                return count / long_probe_distance

        return (count + 1) / long_probe_distance


class Population(SensorBase):
    enabled = True
    name = 'population'
    short_name = 'Pop'

    @classmethod
    def execute(cls, entity, simulator):
        counts = [0, 0]

        def tally_entities(pos):
            counts[0] += 1
            if simulator.entity_at_pos(pos):
                counts[1] += 1

        p = simulator.Parameters
        entity.loc.visit_neighbourhood(p.World.grid_x, p.World.grid_y, p.Simulation.population_sensor_radius,
                                       tally_entities)
        return counts[1] / counts[0]


class PopulationFwd(SensorBase):
    enabled = True
    name = 'population fwd'
    short_name = 'Pfd'

    @classmethod
    def execute(cls, entity, simulator):
        return population_along_axis(entity.loc, entity.prev_dir, simulator)


class PopulationLR(SensorBase):
    enabled = True
    name = 'population LR'
    short_name = 'Plr'

    @classmethod
    def execute(cls, entity, simulator):
        return population_along_axis(entity.loc, entity.prev_dir.rotate90CW(), simulator)


class Age(SensorBase):
    enabled = True
    name = 'age'
    short_name = 'Age'

    @classmethod
    def execute(cls, entity, simulator):
        return entity.age


class Random(SensorBase):
    enabled = True
    name = 'random'
    short_name = 'Rnd'

    @classmethod
    def execute(cls, entity, simulator):
        return simulator.prng.random()


assert sensors.check()
