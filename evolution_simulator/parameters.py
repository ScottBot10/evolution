import os
import typing as t
from os.path import join

import yaml

from .selection_pressure import selection_pressures, SelectionPressure


def _make_vector_node(vector):
    def _vector_node(loader, node):
        value = 0

        data = ()
        if node.id == 'scalar':
            value = loader.construct_scalar(node)
        elif node.id == 'sequence':
            value, *data = loader.construct_sequence(node)
        return vector[value], data

    return _vector_node


yaml.SafeLoader.add_constructor("!SELECTION_PRESSURE", _make_vector_node(selection_pressures))

with open(join(os.path.dirname(__file__), "config.yml"), encoding="UTF-8") as f:
    _CONFIG_YAML = yaml.safe_load(f)


class YAMLGetter(type):
    def __getattr__(cls, name):
        name = name.lower()

        try:
            sections = cls.section.split(".")
            sections.append(name)
            end_section = _CONFIG_YAML
            for section in sections:
                end_section = end_section[section]
            return end_section
        except KeyError:
            raise

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        for name in cls.__annotations__:
            yield name, getattr(cls, name)

    def __dir__(cls):
        return super().__dir__() + list(cls.__annotations__.keys())


class Parameters:
    class World(metaclass=YAMLGetter):
        section = "world"

        grid_x: int
        grid_y: int
        entity_count: int

    class Simulation(metaclass=YAMLGetter):
        section = "simulation"

        selection_pressure: t.Tuple[t.Type[SelectionPressure], t.Optional[t.List]]
        steps_per_generation: int
        long_probe_distance: int
        population_sensor_radius: float

    class Entities(metaclass=YAMLGetter):
        section = "entities"

        genome_length: int
        max_hidden_neurons: int
        responsiveness_curve_kfactor: float
        choose_parents_by_fitness: bool
        sexual_reproduction: bool
        point_mutation_rate: float
        genetic_difference_algorithm: int
