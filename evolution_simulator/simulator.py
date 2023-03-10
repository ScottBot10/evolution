import typing as t
from time import perf_counter

import numpy as np

from .entity import Entity, init_entities
from .entity.genome import NeuralNetwork
from .entity.genome import generate_child_genome
from .models import Coord
from .parameters import Parameters
from .serializer.serializer import SerializerV0
import signal


def false_func(*a, **kw):
    return False


class DelayedKeyboardInterrupt:

    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        print('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


class Simulator:
    def __init__(self, prng, fd):
        self.prng = prng  # TODO: switch to new way of doing numpy random
        self.Parameters: t.Type[Parameters] = Parameters
        self.selection_pressure = self.Parameters.Simulation.selection_pressure(self)
        self.serializer = SerializerV0(fd).Serializer(self.Parameters)

        self.grid = np.zeros((self.Parameters.World.grid_x, self.Parameters.World.grid_y), dtype=np.uint16)  # 65_536

        self.entities = None
        self.init_entities()

        self.move_queue = {}

        self.step = None
        self.generation = 0

    def init_entities(self):  # TODO: maybe move here from entities init
        self.entities = init_entities(self.prng, self.grid, self.Parameters.World.entity_count,
                                      self.Parameters.Entities.genome_length,
                                      self.Parameters.Entities.max_hidden_neurons,
                                      self.Parameters.Entities.responsiveness_curve_kfactor)

    def __getitem__(self, item):
        if isinstance(item, Coord):
            return self.grid[item.x, item.y]
        elif isinstance(item, tuple):
            return self.grid[tuple]
        else:
            return ValueError

    def __setitem__(self, key, value):
        if isinstance(key, Coord):
            self.grid[key.x, key.y] = value
        elif isinstance(key, tuple):
            self.grid[key] = value
        else:
            return ValueError

    def loc_in_bounds(self, loc):
        return 0 <= loc.x < self.Parameters.World.grid_x and 0 <= loc.y < self.Parameters.World.grid_y

    def is_empty(self, loc):
        return self.loc_in_bounds(loc) and not self.entity_at_pos(loc)

    def entity_at_pos(self, pos):
        return self.grid[pos.x, pos.y]

    def run(self, until=None):
        # TODO: add multithreading
        if until is None:
            until = false_func
        while not until(self):
            with DelayedKeyboardInterrupt():
                print('Generation: ', self.generation)
                self.serializer.write_genomes(self.entities)
                self.serializer.write_initial_pos(self.entities)
                start = perf_counter()
                for self.step in range(self.Parameters.Simulation.steps_per_generation):
                    for entity in self.entities:
                        if entity.alive:
                            self.step_entity(entity)
                    if self.selection_pressure.on_step:
                        self.selection_pressure.on_step(self)
                gen_time = perf_counter() - start
                print('Time taken: ', gen_time)
                self.spawn_new_gen(gen_time)
                self.generation += 1
                print()

    def step_entity(self, entity):
        entity.age += 1
        action_levels = entity.nn.feed_forward(entity, self)
        entity.execute_actions(self, action_levels)

    def spawn_new_gen(self, gen_time):
        survival_scores = self.selection_pressure.select(self)
        for entity_index in list(survival_scores.keys()):
            entity = self.entities[entity_index - 1]
            if not entity.nn.connections or not entity.alive:
                survival_scores.pop(entity_index)
        print('Survivors: ', len(survival_scores))
        indexes = [d[0] - 1 for d in sorted(survival_scores.items(), key=lambda d: d[1], reverse=True)]
        genomes = [self.entities[index].genome for index in indexes]
        self.serializer.write_generation(indexes, gen_time)
        self.grid.fill(0)
        if genomes:
            self.create_new_gen(genomes)
        else:
            self.init_entities()

    def create_new_gen(self, genomes):
        grid_shape = m, n = self.grid.shape
        del self.entities
        self.entities = []
        for i, val in enumerate(self.prng.choice(m * n, self.Parameters.World.entity_count, False), start=1):
            loc = np.unravel_index(val, grid_shape)
            self.grid[loc] = i
            genome = generate_child_genome(self.prng, genomes, self.Parameters.Entities.choose_parents_by_fitness,
                                           self.Parameters.Entities.sexual_reproduction,
                                           self.Parameters.Entities.point_mutation_rate)
            self.entities.append(
                Entity(i, Coord(*loc), NeuralNetwork.from_genome(genome, self.Parameters.Entities.max_hidden_neurons),
                       genome,
                       self.prng,
                       self.Parameters.Entities.responsiveness_curve_kfactor))
