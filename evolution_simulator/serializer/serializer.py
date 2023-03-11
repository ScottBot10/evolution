import typing as t
from io import BytesIO
from itertools import zip_longest
from math import ceil
from struct import pack, unpack, calcsize

from .structures import ParamsHeader, ParamsHeaderContainer, Action, DoubleActionContainer, PosStructContainer
from ..models import Coord

if t.TYPE_CHECKING:
    from ..simulator import Simulator
    from ..entity import Entity

BYTE_ORDER = '<'
FILE_THING = b'SBTEVO'
MAIN_HEADER = f'{BYTE_ORDER}{len(FILE_THING)}sB'
MAIN_HEADER_SIZE = calcsize(MAIN_HEADER)

File = t.BinaryIO | t.TextIO
FileOrBytes = bytes | File

SERIALIZERS: t.Dict[int, 'SerializerBaseMeta'] = {}


class SerializerBaseMeta(type):
    Serializer: t.Type['SerializerBase.Serializer']
    Deserializer: t.Type['SerializerBase.Deserializer']
    version: int
    fd: FileOrBytes

    def __new__(mcs, name, bases, attrs):
        cls: 'SerializerBaseMeta' = super().__new__(mcs, name, bases, attrs)
        cls.Serializer.base = cls
        cls.Deserializer.base = cls
        if hasattr(cls, 'version'):
            SERIALIZERS[cls.version] = cls
        return cls


class SerializerBase(metaclass=SerializerBaseMeta):

    def __init__(self, fd: File):
        self.fd = fd
        self.Serializer.base = self
        self.Deserializer.base = self

    class Serializer:
        base: t.Type['SerializerBase']

        def __init__(self, Parameters):
            self.fd = self.base.fd
            self.Parameters = Parameters

        def initialize_entity_actions(self):
            pass

        def write_genomes(self, entities: t.List['Entity']):
            pass

        def entity_move(self, entity: 'Entity', sim: 'Simulator', offset: 'Coord'):
            pass

        def write_initial_pos(self, entities: t.List['Entity']):
            pass

        def write_generation(self, indexes: t.List[int], time: float):
            pass

    class Deserializer:
        base: t.Type['SerializerBase']

        def __init__(self):
            self.fd = self.base.fd
            self.generation_size = None

        def read_genomes(self):
            pass

        def read_initial_pos(self):
            pass

        def read_step(self):
            pass

        def skip_stats(self):
            pass


class SerializerV0(SerializerBase):
    version = 0
    params_size = 'Q'
    full_header = MAIN_HEADER + params_size
    stat_format = BYTE_ORDER + 'Lf'

    class Serializer(SerializerBase.Serializer):
        base: t.Type['SerializerV0']

        def __init__(self, Parameters):
            super().__init__(Parameters)
            self.entity_actions = None
            self.entity_count = Parameters.World.entity_count
            self.steps_per_generation = Parameters.Simulation.steps_per_generation
            self.genome_length = Parameters.Entities.genome_length

            self.genome_format = BYTE_ORDER + ('L' * self.genome_length)
            self.pos_format = BYTE_ORDER + 'H' * self.Parameters.World.entity_count

            self.initialize_entity_actions()

            params_header = ParamsHeaderContainer(
                ParamsHeader(
                    grid=PosStructContainer((self.Parameters.World.grid_x, self.Parameters.World.grid_y)).asdecimal,
                    entityCount=self.Parameters.World.entity_count,
                    generationSteps=self.Parameters.Simulation.steps_per_generation,
                    genomeLength=self.Parameters.Entities.genome_length,
                    hiddenNeurons=self.Parameters.Entities.max_hidden_neurons,
                    mutationRate=int(self.Parameters.Entities.point_mutation_rate * 1000)))

            self.fd.write(pack(self.base.full_header, FILE_THING, self.base.version, params_header.asdecimal))

        def initialize_entity_actions(self):
            self.entity_actions = [
                [None for __ in range(self.Parameters.World.entity_count)]
                for _ in range(self.Parameters.Simulation.steps_per_generation)
            ]

        def write_genomes(self, entities: t.List['Entity']):
            for entity in entities:
                self.fd.write(pack(self.genome_format, *(gene.asdecimal for gene in entity.genome)))

        def entity_move(self, entity: 'Entity', sim: 'Simulator', offset: 'Coord'):
            self.entity_actions[sim.step][entity.index - 1] = offset.to_action()

        def write_initial_pos(self, entities: t.List['Entity']):
            self.fd.write(pack(
                self.pos_format,
                *(
                    PosStructContainer((entity.loc.x, entity.loc.y)).asdecimal
                    for entity in entities
                )
            ))

        def write_generation(self, indexes: t.List[int], time: float):
            for step in self.entity_actions:
                k = zip_longest(step[::2], step[1::2])
                l = [
                    DoubleActionContainer.from_actions(a1 or Action(), a2 or Action()).asdecimal
                    for a1, a2 in k
                ]
                self.fd.write(pack(BYTE_ORDER + 'B' * ceil(self.Parameters.World.entity_count / 2),
                                   *l))
            self.fd.write(pack(self.base.stat_format, len(indexes), time))

            self.initialize_entity_actions()

    class Deserializer(SerializerBase.Deserializer):
        base: t.Type['SerializerV0']

        def __init__(self):
            super().__init__()
            self.param_format = BYTE_ORDER + self.base.params_size
            self.param_size = calcsize(self.param_format)

            params, *_ = unpack(self.param_format, self.fd.read(self.param_size))
            self.params = ParamsHeaderContainer(asdecimal=params).b

            self.grid = PosStructContainer(asdecimal=self.params.grid).b

            self.mutation_rate = self.params.mutationRate / 1000
            self.odd_enemies = self.params.entityCount % 2 == 0
            self.action_count = ceil(self.params.entityCount / 2)

            self.genome_size = calcsize(BYTE_ORDER + ('L' * self.params.genomeLength))

            self.generation_format = BYTE_ORDER + 'B' * self.action_count
            self.generation_size = calcsize(self.generation_format)

            self.init_pos_format = BYTE_ORDER + 'H' * self.params.entityCount
            self.init_pos_size = calcsize(self.init_pos_format)

            self.stat_size = calcsize(self.base.stat_format)

            self.generation_size_no_stats = (self.genome_size * self.params.entityCount) + \
                                            self.init_pos_size + \
                                            (self.generation_size * self.params.generationSteps)
            self.generation_size_stats = self.generation_size_no_stats + self.stat_size

        def read_stats(self):
            self.fd.read(self.generation_size_no_stats)
            data = self.fd.read(self.stat_size)
            if data:
                stats = unpack(self.base.stat_format, data)
                self.fd.seek(-self.generation_size_stats, 1)
                return stats
            else:
                return None

        def read_genomes(self):
            dat = self.fd.read(self.genome_size * self.params.entityCount)

        def read_initial_pos(self):
            data = self.fd.read(self.init_pos_size)
            if data:
                return [
                    Coord.from_pos_struct(PosStructContainer(asdecimal=pos).b)
                    for pos in unpack(self.init_pos_format, data)
                ]
            else:
                return

        def read_step(self):
            entity_actions = []
            for i, action in enumerate(unpack(self.generation_format, self.fd.read(self.generation_size))):
                a1, a2 = DoubleActionContainer(asdecimal=action).to_actions()
                entity_actions.append(Coord.from_action(a1))
                if i != self.action_count or not self.odd_enemies:
                    entity_actions.append(Coord.from_action(a2))
            return entity_actions

        def skip_stats(self):
            self.fd.seek(self.stat_size, 1)


def get_serializer(fd: FileOrBytes) -> SerializerBaseMeta:
    if isinstance(fd, bytes):
        fd = BytesIO(fd)
    header = fd.read(MAIN_HEADER_SIZE)
    if len(header) == MAIN_HEADER_SIZE:
        file_thing, version = unpack(MAIN_HEADER, header)
        if file_thing == FILE_THING:
            return SERIALIZERS.get(version)(fd)
