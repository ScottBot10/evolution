# TODO: Fix properly. This is a quick fix for the circular import error (sensor_vectors imports from genome and
#  neural_network imports from sensor_vectors)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .genome.genome import Genome

from ctypes import sizeof


def jaro_winkler(genome1: 'Genome', genome2: 'Genome'):
    pass


def hamming_bits(genome1: 'Genome', genome2: 'Genome'):
    bit_difference = 0
    genome_len = len(genome1)
    assert genome_len and genome_len == len(genome2)
    for gene1, gene2 in zip(genome1, genome2):
        bit_difference += (gene1.asdecimal ^ gene2.asdecimal).bit_count()

    return 1 - min(1, (2 * bit_difference) / (genome_len * sizeof(gene1) * 8))


def hamming_bytes(genome1: 'Genome', genome2: 'Genome'):
    pass
