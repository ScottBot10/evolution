import ctypes
import typing as t
from ctypes import c_uint32

from ...serializer.structures import BytesConvertable

NEURON = 0  # input or output
SENSOR = 1  # input
ACTION = 1  # output


class Gene(ctypes.LittleEndianStructure, BytesConvertable):
    # _pack_ = 1
    _fields_ = [
        ("inputType", c_uint32, 1),  # NEURON or SENSOR
        ("inputNum", c_uint32, 7),
        ("outputType", c_uint32, 1),  # NEURON or ACTION
        ("outputNum", c_uint32, 7),
        ("weight", ctypes.c_int32, 16)
    ]

    def float_weight(self):
        return self.weight / 8192

    def __repr__(self):
        data = ', '.join(f'{name}={getattr(self, name)!r}' for name, *_ in self._fields_)
        return f'{self.__class__.__qualname__}({data})'

    def __eq__(self, o):
        return isinstance(o, self.__class__) and self._fields_ == o._fields_ and self.to_bytes() == o.to_bytes()

    @classmethod
    def random(cls, prng):
        return cls(prng.integers(2), prng.integers(128), prng.integers(2), prng.integers(128),
                   prng.integers(-0x8000, 0x8000))


class GeneContainer(ctypes.Union):
    _fields_ = [
        ("b", Gene),
        ("asdecimal", c_uint32)
    ]


Genome = t.List[Gene]


def mutate_genome(genome: Genome, prng, point_mutation_rate):
    for _ in range(len(genome)):
        if prng.random() < point_mutation_rate:
            index = prng.integers(len(genome))
            gene = genome[index]
            chance = prng.integers(5)
            if chance == 0:
                gene.inputType ^= 1
            elif chance == 1:
                gene.outputType ^= 1
            elif chance == 2:
                gene.inputNum ^= (1 << prng.integers(8))
            elif chance == 3:
                gene.outputNum ^= (1 << prng.integers(8))
            elif chance == 4:
                gene.weight ^= (1 << prng.integers(1, 16))


def copy_genome(genome: Genome):
    return [Gene.from_bytes(gene.to_bytes()) for gene in genome]


def generate_child_genome(prng, genomes: t.List[Genome], by_fitness: bool, sexual_reproduction: bool,
                          point_mutation_rate: float):
    genomes_length = len(genomes)
    if by_fitness and genomes_length > 1:
        parent1 = prng.integers(1, genomes_length)
        parent2 = prng.integers(0, parent1)
    else:
        parent1 = prng.integers(0, genomes_length)
        parent2 = prng.integers(0, genomes_length)

    genome1 = copy_genome(genomes[parent1])

    if sexual_reproduction:
        genome2 = copy_genome(genomes[parent2])
        shorter, genome = sorted((genome1, genome2), key=len)
        shorter_len = len(shorter)
        index1 = prng.integers(0, shorter_len)
        index2 = prng.integers(index1, shorter_len)

        for i in range(index1, index2 + 1):
            genome[i] = shorter[i]
    else:
        genome = genome1
    mutate_genome(genome, prng, point_mutation_rate)
    return genome
