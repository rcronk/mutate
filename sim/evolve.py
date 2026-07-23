""" evolve.py - mutation and selection over program genomes.

The same plain loop as ridge.evolve, but the genome is now Python source and its
fitness is the single-creature reproductive assay (sim.life). Selection sees only
that score, which is survival and reproduction value, never a target program or
behaviour. Nothing aims: the loop keeps whatever reproduces better and mutates
it. Selecting on reproduction is not the rigged kind of goal (there is no target
to match), it is the one pressure that exists in biology.

Offspring mutation is whole-genome: with probability mutation_rate an offspring
is a single mutation of its parent, otherwise an exact copy, matching the per-
genome mutation framing used in Part A. Scores are cached by source, because a
population is mostly identical copies.
"""

import dataclasses
import random

from sim import life, substrate


@dataclasses.dataclass
class Result:
    """ What one run produced. """
    best_source: str
    best_score: int
    history: list
    generations: int


def _tournament(population, scores, rng, size=3):
    """ :return: The fitter of a few random genomes (the source itself) """
    best = rng.randrange(len(population))
    for _ in range(size - 1):
        challenger = rng.randrange(len(population))
        if scores[challenger] > scores[best]:
            best = challenger
    return population[best]


# Six knobs, all keyword-only and each a distinct run parameter; bundling them
# would only add indirection.
def run(*, population_size, generations, mutation_rate,  # pylint: disable=too-many-arguments
        seed, ancestor=substrate.ANCESTOR, fitness=life.reproductive_output):
    """ Evolves a population of programs under reproductive selection.
    :param population_size: How many programs per generation
    :param generations: How many generations to run
    :param mutation_rate: Probability an offspring is mutated rather than copied
    :param seed: Random seed; the same seed reproduces the run
    :param ancestor: The founding program every genome starts as
    :param fitness: The selection measure, a callable from source to a score;
        the solo assay by default, or the competitive environment for a run
        where complexity has to pay
    :return: A Result, whose history is the best score in each generation
        including the founding one
    """
    rng = random.Random(seed)
    cache = {}

    def score(source):
        if source not in cache:
            cache[source] = fitness(source)
        return cache[source]

    population = [ancestor] * population_size
    scores = [score(source) for source in population]
    history = [max(scores)]

    for _ in range(generations):
        offspring = []
        for _ in range(population_size):
            parent = _tournament(population, scores, rng)
            if rng.random() < mutation_rate:
                offspring.append(substrate.mutate_once(parent, rng.randrange(2 ** 32)))
            else:
                offspring.append(parent)
        population = offspring
        scores = [score(source) for source in population]
        history.append(max(scores))

    best = max(range(population_size), key=lambda index: scores[index])
    return Result(best_source=population[best], best_score=scores[best],
                  history=history, generations=generations)
