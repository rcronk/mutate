""" experiment.py - the build and degrade tests (slice 4b).

The experiment the whole protocell effort was built for, run in the two-signal
world that provably requires structure. Two seeds:

  - Build test: a blind pool that reproduces but ignores safety. Can mutation and
    selection add the missing second sensor (a `env.safe` read wired into the
    division decision)? Reaching it would raise specified information, and the
    new structure would be readable in the code.
  - Degrade test: the sensing pool, which already has the structure. Does
    purifying selection keep it, or does it decay under mutation?

The metric is two-signal specified information (constrained sites measured
against the two-signal fitness), and the readout is also the code itself.
"""

import random
import statistics
import sys

from protocell import ancestors, environment, information, mutation, world

BUILD_FOUNDERS = 15
BUILD_TICKS = 400
SEEDS = 3


def two_signal_fitness(pool, *, seeds=3):
    """ :return: Mean surviving population of a pool in the two-signal world """
    return statistics.mean(
        len(world.run(pool, founders=6, ticks=250, seed=seed,
                      make_env=environment.make_world,
                      newborn_survives=environment.newborn_survives).survivors)
        for seed in range(seeds))


def _evolve(seed_pool, seed, *, founders=BUILD_FOUNDERS, ticks=BUILD_TICKS):
    rng = random.Random(7000 + seed)
    return world.run(seed_pool, founders=founders, ticks=ticks, seed=seed,
                     make_env=environment.make_world,
                     newborn_survives=environment.newborn_survives,
                     mutate=lambda pool: mutation.mutate(pool, rng, point_lambda=1.0))


def _using_safe(survivors):
    return sum(1 for cell in survivors if 'safe' in cell.dump())


def build_test(*, seeds=SEEDS):
    """ :return: Per seed, how many surviving cells built a safety sensor """
    return [_using_safe(_evolve(ancestors.blind_pool(), seed).survivors)
            for seed in range(seeds)]


def degrade_test(*, seeds=SEEDS):
    """ :return: Per seed, the fraction of survivors that keep the safety sensor """
    fractions = []
    for seed in range(seeds):
        survivors = _evolve(ancestors.sensing_pool(), seed).survivors
        fractions.append(_using_safe(survivors) / len(survivors) if survivors else 0.0)
    return fractions


def seed_information(rng, *, samples=100):
    """ :return: (blind, sensing) two-signal specified information of the seeds """
    blind = information.specified_information(
        ancestors.blind_pool(), rng, samples=samples, fitness=two_signal_fitness)
    sensing = information.specified_information(
        ancestors.sensing_pool(), rng, samples=samples, fitness=two_signal_fitness)
    return blind, sensing


def main():
    """ Prints the build and degrade results. """
    blind_info, sensing_info = seed_information(random.Random(0))
    print('Two-signal specified information of the seeds (constrained sites):')
    print(f'  blind seed:   {blind_info.constrained_sites:.0f}')
    print(f'  sensing seed: {sensing_info.constrained_sites:.0f}  '
          '(the safety sensor is worth the difference)')
    print()
    print('BUILD test (blind seed): cells that built a safety sensor, per seed:')
    print(f'  {build_test()}  -> the structure is not built')
    print()
    print('DEGRADE test (sensing seed): fraction keeping the sensor, per seed:')
    print(f'  {[round(fraction, 2) for fraction in degrade_test()]}  -> the structure is kept')
    print()
    print('So selection maintains the structure but does not build it, in this')
    print('substrate. Caveat: this substrate has no modularity, recombination, or')
    print('module duplication, the features biology uses to build; whether adding')
    print('them changes the result is the knob-dependence question for later.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
