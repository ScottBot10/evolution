import typing as t
from io import BytesIO
from itertools import zip_longest
from math import ceil
from struct import Struct, calcsize

from .structures import ParamsHeader, ParamsHeader_size, PosStruct, DoubleAction, UINT16_STRUCT, UINT8_STRUCT
from ..models import Coord
from ..selection_pressure import selection_pressures

if t.TYPE_CHECKING:
    from ..simulator import Simulator
    from ..entity import Entity

BYTE_ORDER = '<'
FILE_THING = b'SBTEVO'
MAIN_HEADER = Struct(f'{BYTE_ORDER}{len(FILE_THING)}sB')

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

        def __init__(self, simulator, Parameters):
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
    stat_format = Struct(f'{BYTE_ORDER}Lf')

    class Serializer(SerializerBase.Serializer):
        base: t.Type['SerializerV0']

        def __init__(self, simulator, Parameters):
            super().__init__(simulator, Parameters)

            self.fd.write(MAIN_HEADER.pack(FILE_THING, self.base.version))

            self.entity_actions = None
            self.entity_count = Parameters.World.entity_count
            self.steps_per_generation = Parameters.Simulation.steps_per_generation
            self.genome_length = Parameters.Entities.genome_length

            self.genome_format = Struct(f"{BYTE_ORDER}{self.genome_length}L")
            self.pos_format = Struct(f"{BYTE_ORDER}{self.Parameters.World.entity_count}H")
            self.generation_format = Struct(f"{BYTE_ORDER}{ceil(self.Parameters.World.entity_count / 2)}B")

            self.initialize_entity_actions()

            params_header = ParamsHeader(
                grid=PosStruct(self.Parameters.World.grid_x, self.Parameters.World.grid_y),
                entityCount=self.Parameters.World.entity_count,
                generationSteps=self.Parameters.Simulation.steps_per_generation,
                genomeLength=self.Parameters.Entities.genome_length,
                hiddenNeurons=self.Parameters.Entities.max_hidden_neurons,
                mutationRate=int(self.Parameters.Entities.point_mutation_rate * 65_536),
                selectionPressure=simulator.selection_pressure.id,
                selectionPressureData=simulator.selection_pressure.to_data()
            )

            self.fd.write(params_header.to_bytes())

        def initialize_entity_actions(self):
            self.entity_actions = [
                [None for __ in range(self.Parameters.World.entity_count)]
                for _ in range(self.Parameters.Simulation.steps_per_generation)
            ]

        def write_genomes(self, entities: t.List['Entity']):
            for entity in entities:
                self.fd.write(b''.join(gene.to_bytes() for gene in entity.genome))

        def entity_move(self, entity: 'Entity', sim: 'Simulator', offset: 'Coord'):
            self.entity_actions[sim.step][entity.index - 1] = offset

        def write_initial_pos(self, entities: t.List['Entity']):
            self.fd.write(b''.join(
                PosStruct(entity.loc.x, entity.loc.y).to_bytes()
                for entity in entities
            ))

        def write_generation(self, indexes: t.List[int], time: float):
            for step in self.entity_actions:
                k = zip_longest(step[::2], step[1::2])
                l = [
                    DoubleAction(offset1.x if offset1 is not None else 0,
                                 offset1.y if offset1 is not None else 0,
                                 offset2.x if offset2 is not None else 0,
                                 offset2.y if offset2 is not None else 0).to_bytes()
                    for offset1, offset2 in k
                ]
                self.fd.write(b''.join(l))
            self.fd.write(self.base.stat_format.pack(len(indexes), time))

            self.initialize_entity_actions()

    class Deserializer(SerializerBase.Deserializer):
        base: t.Type['SerializerV0']

        def __init__(self):
            super().__init__()

            self.params = ParamsHeader.from_bytes(self.fd.read(ParamsHeader_size))

            self.mutation_rate = self.params.mutationRate / 65_536
            self.odd_enemies = self.params.entityCount % 2 == 0
            self.action_count = ceil(self.params.entityCount / 2)

            self.selection_pressure = selection_pressures[self.params.selectionPressure].from_data(
                self.params.selectionPressureData)

            self.genome_size = calcsize(f'{BYTE_ORDER}{self.params.genomeLength}L')

            self.generation_format = Struct(f'{BYTE_ORDER}{self.action_count}B')

            self.init_pos_format = Struct(f'{BYTE_ORDER}{self.params.entityCount}H')

            self.generation_size_no_stats = (self.genome_size * self.params.entityCount) + \
                                            self.init_pos_format.size + \
                                            (self.generation_format.size * self.params.generationSteps)
            self.generation_size_stats = self.generation_size_no_stats + self.base.stat_format.size

        def read_stats(self):
            self.fd.read(self.generation_size_no_stats)
            data = self.fd.read(self.base.stat_format.size)
            if data:
                stats = self.base.stat_format.unpack(data)
                self.fd.seek(-self.generation_size_stats, 1)
                return stats
            else:
                return None

        def read_genomes(self):
            dat = self.fd.read(self.genome_size * self.params.entityCount)

        def _read_chunks(self, total_size, chunk_size):
            data = self.fd.read(total_size)
            return [
                data[i:i + chunk_size]
                for i in range(0, total_size, chunk_size)
            ]

        def read_initial_pos(self):
            return [
                Coord.from_pos_struct(PosStruct.from_bytes(chunk))
                for chunk in self._read_chunks(self.init_pos_format.size, 2)
            ]

        def read_step(self):
            entity_actions = []
            for i, chunk in enumerate(self.fd.read(self.generation_format.size)):
                UINT8_STRUCT.pack_into(double_action := DoubleAction(), 0, chunk)

                entity_actions.append(Coord(double_action.moveX1, double_action.moveY1))
                if i != self.action_count or not self.odd_enemies:
                    entity_actions.append(Coord(double_action.moveX2, double_action.moveY2))
            return entity_actions

        def skip_stats(self):
            self.fd.seek(self.base.stat_format.size, 1)


def get_serializer(fd: FileOrBytes) -> SerializerBaseMeta:
    if isinstance(fd, bytes):
        fd = BytesIO(fd)
    header = fd.read(MAIN_HEADER.size)
    if len(header) == MAIN_HEADER.size:
        file_thing, version = MAIN_HEADER.unpack(header)
        if file_thing == FILE_THING:
            return SERIALIZERS.get(version)(fd)
