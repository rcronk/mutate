""" evolve.py - the plainest mutation-and-selection loop.

A population of binary genomes, tournament selection on fitness, and per-part
mutation. Deliberately unclever: the experiment's whole point is to watch what
ordinary cumulative selection does as the landscape's gap widens, so the
algorithm must not be doing anything special.

Note what selection is and is not given. It sees each genome's fitness, which is
survival value, and nothing else. It is never told the target or which parts are
still wrong. It cannot aim. It can only keep whatever currently scores higher,
which is exactly the blind, foresightless process under test.
"""

import dataclasses
import random


@dataclasses.dataclass
class Result:
    """ What one run produced. """
    solved: bool
    solved_at: int
    best_fitness: int
    generations: int


def _tournament(population, fitnesses, rng, size=3):
    """ Picks the fitter of a few random genomes.

        Tournament selection rather than fitness-proportionate, because it
        handles a flat plateau gracefully: when everyone on the plateau ties, it
        reduces to a random pick, which is precisely the neutral drift that a
        population uses to explore a no-benefit gap.
    :return: A copy of the winning genome
    """
    best_index = rng.randrange(len(population))
    for _ in range(size - 1):
        challenger = rng.randrange(len(population))
        if fitnesses[challenger] > fitnesses[best_index]:
            best_index = challenger
    return list(population[best_index])


def _mutate(genome, mutation_rate, rng):
    """ Flips each part independently with probability mutation_rate.
    :return: The mutated genome
    """
    return [1 - part if rng.random() < mutation_rate else part for part in genome]


def run(landscape, *, population_size, generations, mutation_rate, seed):
    """ Evolves a population against a landscape until it is solved or the
        generation budget runs out.
    :param landscape: A Landscape
    :param population_size: How many genomes
    :param generations: The budget
    :param mutation_rate: Per-part flip probability
    :param seed: Random seed; the same seed reproduces the run
    :return: A Result
    """
    rng = random.Random(seed)
    population = [[0] * landscape.n_parts for _ in range(population_size)]
    best_fitness = 0

    for generation in range(generations):
        fitnesses = [landscape.fitness(genome) for genome in population]
        best_fitness = max(best_fitness, *fitnesses)
        if best_fitness == landscape.max_fitness:
            return Result(solved=True, solved_at=generation,
                          best_fitness=best_fitness, generations=generations)
        population = [_mutate(_tournament(population, fitnesses, rng), mutation_rate, rng)
                      for _ in range(population_size)]

    return Result(solved=False, solved_at=None,
                  best_fitness=best_fitness, generations=generations)
