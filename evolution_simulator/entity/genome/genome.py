import ctypes
import typing as t
from ctypes import c_uint32

NEURON = 0  # input or output
SENSOR = 1  # input
ACTION = 1  # output


class Gene(ctypes.LittleEndianStructure):
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


class GeneContainer(ctypes.Union):
    _fields_ = [
        ("b", Gene),
        ("asdecimal", c_uint32)
    ]

    def __eq__(self, o):
        if isinstance(o, self.__class__) and self.b._fields_ == o.b._fields_ and self.asdecimal == o.asdecimal:
            return all(
                getattr(self.b, field_name) == getattr(o.b, field_name) for field_name, _, _ in self.b._fields_
            )
        return False

    @classmethod
    def random(cls, prng):
        return cls(
            Gene(prng.randint(0, 2), prng.randint(0, 128), prng.randint(0, 2), prng.randint(0, 128),
                 prng.randint(-0x8000, 0x8000)))


Genome = t.List[GeneContainer]


def mutate_genome(genome: Genome, prng, point_mutation_rate):
    for _ in range(len(genome)):
        if prng.random() < point_mutation_rate:
            index = prng.randint(len(genome))
            gene = genome[index].b
            chance = prng.randint(5)
            if chance == 0:
                gene.inputType ^= 1
            elif chance == 1:
                gene.outputType ^= 1
            elif chance == 2:
                gene.inputNum ^= (1 << prng.randint(8))
            elif chance == 3:
                gene.outputNum ^= (1 << prng.randint(8))
            elif chance == 4:
                gene.weight ^= (1 << prng.randint(1, 16))


def copy_genome(genome: Genome):
    return [GeneContainer(asdecimal=gene.asdecimal) for gene in genome]


def generate_child_genome(prng, genomes: t.List[Genome], by_fitness: bool, sexual_reproduction: bool,
                          point_mutation_rate: float):
    genomes_length = len(genomes)
    if by_fitness and genomes_length > 1:
        parent1 = prng.randint(1, genomes_length)
        parent2 = prng.randint(0, parent1)
    else:
        parent1 = prng.randint(0, genomes_length)
        parent2 = prng.randint(0, genomes_length)

    genome1 = copy_genome(genomes[parent1])

    if sexual_reproduction:
        genome2 = copy_genome(genomes[parent2])
        shorter, genome = sorted((genome1, genome2), key=len)
        shorter_len = len(shorter)
        index1 = prng.randint(0, shorter_len)
        index2 = prng.randint(index1, shorter_len)

        for i in range(index1, index2 + 1):
            genome[i] = shorter[i]
    else:
        genome = genome1
    mutate_genome(genome, prng, point_mutation_rate)
    return genome
