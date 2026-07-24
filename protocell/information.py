""" information.py - specified (functional) information of a protein pool.

The north-star measurement. Specified information is the amount of the genome
that is *constrained by function*: positions where a mutation reduces fitness
(purifying selection). Random or junk text has high Shannon entropy but low
specified information; we measure the latter, by mutation sensitivity, exactly
as ridge.dfe did for real proteins.

Two numbers matter:
  - `deleterious_fraction`: the share of single mutations that reduce fitness.
    It falls when junk accumulates, because junk positions are free to change.
  - `constrained_sites` (fraction x genome length): the absolute amount of
    functional information. Adding junk does not raise it, because junk is not
    constrained. This is the quantity whose *direction* over generations answers
    the build-versus-degrade question.

Fitness is a standardized assay: the total divisions of a single founder lineage
in a fixed, scarce world, averaged over a few seeds so a single unlucky run does
not label a neutral mutation deleterious.
"""

import dataclasses
import statistics

from protocell import mutation, world
from protocell.protein import Protein

ASSAY_FOOD = 30
ASSAY_REGROWTH = 8
ASSAY_TICKS = 100
ASSAY_SEEDS = 3
DEFAULT_SAMPLES = 200


@dataclasses.dataclass
class SpecifiedInfo:
    """ How much of a pool is constrained by function. """
    fitness: float
    deleterious_fraction: float
    genome_length: int

    @property
    def constrained_sites(self):
        """ :return: Estimated positions under purifying selection, the
            specified-information measure """
        return self.deleterious_fraction * self.genome_length


def assay(pool, *, seeds=ASSAY_SEEDS):
    """ Standardized fitness: mean lineage divisions in a fixed scarce world.
    :return: The mean number of divisions over `seeds` runs
    """
    return statistics.mean(
        world.run(pool, founders=1, ticks=ASSAY_TICKS, food=ASSAY_FOOD,
                  regrowth=ASSAY_REGROWTH, seed=seed).generations
        for seed in range(seeds))


def _genome_length(pool):
    return sum(len(protein.source) for protein in pool)


def specified_information(pool, rng, *, samples=DEFAULT_SAMPLES, seeds=ASSAY_SEEDS):
    """ Estimates the specified information of a pool by mutation sensitivity.

        Draws `samples` single-character substitutions from across the genome and
        counts how many reduce the assay fitness. The constrained-site estimate
        is that fraction times the genome length.
    :param pool: A list of Proteins
    :param rng: A random.Random, for reproducibility
    :return: A SpecifiedInfo
    """
    baseline = assay(pool, seeds=seeds)
    length = _genome_length(pool)
    if length == 0:
        return SpecifiedInfo(fitness=baseline, deleterious_fraction=0.0,
                             genome_length=0)
    deleterious = 0
    for _ in range(samples):
        index = rng.randrange(len(pool))
        source = pool[index].source
        if not source:
            continue
        position = rng.randrange(len(source))
        mutated = source[:position] + rng.choice(mutation.ALPHABET) + source[position + 1:]
        candidate = list(pool)
        candidate[index] = Protein(mutated)
        if assay(candidate, seeds=seeds) < baseline:
            deleterious += 1
    return SpecifiedInfo(fitness=baseline, deleterious_fraction=deleterious / samples,
                         genome_length=length)
