import typing as t
from abc import ABC
from io import BytesIO
from struct import pack, unpack, calcsize

from .structures import ParamsHeader, ParamsHeaderContainer, Action, ActionContainer

if t.TYPE_CHECKING:
    from ..simulator import Simulator
    from ..entity import Entity
    from ..models import Coord

BYTE_ORDER = '<'
FILE_THING = b'SBTEVO'
MAIN_HEADER = f'{BYTE_ORDER}{len(FILE_THING)}sB'
MAIN_HEADER_SIZE = calcsize(MAIN_HEADER)

FileOrBytes = t.Union[bytes, t.BinaryIO]


class SerializerBase(ABC):
    version = None

    def __init__(self, fd: t.BinaryIO, Parameters):
        self.fd = fd
        self.Parameters = Parameters

    def write_genomes(self, entities: t.List['Entity']):
        raise NotImplementedError

    def entity_move(self, entity: 'Entity', sim: 'Simulator', offset: 'Coord'):
        return NotImplementedError

    def write_generation(self, indexes: t.List[int], time: float):
        return NotImplementedError


class DeserializerBase(ABC):
    version = None

    params = None

    def __init__(self, fd: t.BinaryIO):
        self.fd = fd


class SerializerV0(SerializerBase):
    version = 0
    full_header = MAIN_HEADER + 'Q'

    def __init__(self, fd: t.BinaryIO, Parameters):
        super().__init__(fd, Parameters)
        self.entity_actions = None
        self.entity_count = Parameters.World.entity_count
        self.steps_per_generation = Parameters.Simulation.steps_per_generation
        self.genome_length = Parameters.Entities.genome_length

        self.genome_format = BYTE_ORDER + ('L' * self.genome_length)

        self.initialize_entity_actions()

        params_header = ParamsHeaderContainer(
            ParamsHeader(gridX=self.Parameters.World.grid_x, gridY=self.Parameters.World.grid_y,
                         entityCount=self.Parameters.World.entity_count,
                         generationSteps=self.Parameters.Simulation.steps_per_generation,
                         genomeLength=self.Parameters.Entities.genome_length,
                         hiddenNeurons=self.Parameters.Entities.max_hidden_neurons,
                         mutationRate=int(self.Parameters.Entities.point_mutation_rate * 1000)))

        self.fd.write(pack(self.full_header, FILE_THING, self.version, params_header.asdecimal))

    def initialize_entity_actions(self):
        self.entity_actions = \
            [[None] * self.Parameters.World.entity_count] \
            * self.Parameters.Simulation.steps_per_generation

    def write_genomes(self, entities: t.List['Entity']):
        for entity in entities:
            self.fd.write(pack(self.genome_format, *(gene.asdecimal for gene in entity.genome)))

    def entity_move(self, entity: 'Entity', sim: 'Simulator', offset: 'Coord'):
        self.entity_actions[sim.step][entity.index - 1] = ActionContainer((offset.x, offset.y))

    def write_generation(self, indexes: t.List[int], time: float):
        for step in self.entity_actions:
            self.fd.write(pack(BYTE_ORDER + 'B' * self.Parameters.World.entity_count,
                               *((action if action is not None else ActionContainer()).asdecimal for action in step)))
        self.fd.write(pack(BYTE_ORDER + 'Lf', len(indexes), time))
        return super().write_generation(indexes, time)


class DeserializerV0(DeserializerBase):
    version = 0

    params_format = BYTE_ORDER + 'Q'

    def __init__(self, fd: t.BinaryIO):
        super().__init__(fd)
        params, *_ = unpack(self.params_format, self.fd.read(calcsize(self.params_format)))
        self.params = ParamsHeaderContainer(asdecimal=params).b
        self.mutation_rate = self.params.mutationRate / 1000


VERSIONS: t.Dict[int, t.Type[DeserializerBase]] = {
    0: DeserializerV0
}


def get_deserializer(fd: FileOrBytes) -> DeserializerBase:
    if isinstance(fd, bytes):
        fd = BytesIO(fd)
    header = fd.read(MAIN_HEADER_SIZE)
    if len(header) == MAIN_HEADER_SIZE:
        file_thing, version = unpack(MAIN_HEADER, header)
        if file_thing == FILE_THING:
            deserializer = VERSIONS.get(version)
            if deserializer is not None:
                return deserializer(fd)


def main():
    print()
