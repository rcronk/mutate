""" experiment.py - the headline sweep for Part A.

Three questions, each answered by holding everything fixed but one variable:

  1. Does part count matter?  Vary N with a tiny gap. If success stays high,
     complexity is not the barrier.

  2. Does a neutral gap matter?  Vary g with valley_depth 0. Drift crosses these,
     so success should hold until the block space (2^g) outgrows the budget.

  3. Does a valley matter?  Vary g with valley_depth > 0. Selection opposes
     crossing, so success should collapse fast, at a much smaller g.

Run: python -m ridge.experiment
"""

import sys

from ridge import evolve, landscape

SEEDS = range(10)


# Six independent sweep knobs, all varied across the three experiments.
def _success_rate(*, n_parts, coordination_degree, valley_depth,  # pylint: disable=too-many-arguments
                  population_size, generations, mutation_rate):
    """ Fraction of seeds that reach the target. """
    land = landscape.Landscape(n_parts, coordination_degree, valley_depth)
    solved = sum(evolve.run(land, population_size=population_size,
                            generations=generations, mutation_rate=mutation_rate,
                            seed=seed).solved
                 for seed in SEEDS)
    return solved / len(SEEDS)


def _line(label, value, rate):
    meter = '#' * round(rate * 20)
    print(f'  {label} {value:>3}   {rate:>5.0%}  {meter}')


def part_count_does_not_matter():
    """ Vary N with a tiny gap. Success should stay flat.

        Mutation is held constant per *genome* (rate = 1/N), not per part, which
        is how biology works: an organism's genome-wide mutation count is roughly
        fixed regardless of genome size. A fixed per-part rate would instead pile
        on mutation load as N grows and hit the error threshold, which is a
        different effect entirely and would confound this measurement.
    """
    print('1. Part count, with a tiny gap (g=2, neutral), mutation held per '
          'genome. Success vs N:')
    for n_parts in (8, 16, 32, 64, 128):
        rate = _success_rate(n_parts=n_parts, coordination_degree=2, valley_depth=0,
                             population_size=100, generations=6000,
                             mutation_rate=1.0 / n_parts)
        _line('N =', n_parts, rate)


def neutral_gaps_are_crossable():
    """ Vary g with valley_depth 0. Success holds for a while, then drift runs
        out of budget. """
    print('\n2. Neutral gap width g (valley_depth=0). Success vs g:')
    for gap in (2, 6, 10, 14, 18):
        rate = _success_rate(n_parts=gap + 6, coordination_degree=gap, valley_depth=0,
                             population_size=200, generations=4000, mutation_rate=0.06)
        _line('g =', gap, rate)


def valleys_are_the_barrier():
    """ Vary g with a valley. Success should collapse far sooner. """
    print('\n3. Deleterious valley width g (valley_depth=3). Success vs g:')
    for gap in (2, 4, 6, 8, 10):
        rate = _success_rate(n_parts=gap + 6, coordination_degree=gap, valley_depth=3,
                             population_size=200, generations=4000, mutation_rate=0.06)
        _line('g =', gap, rate)


def main():
    """ Runs the three sweeps. """
    part_count_does_not_matter()
    neutral_gaps_are_crossable()
    valleys_are_the_barrier()
    print('\nReading: part count barely moves success; a neutral gap is crossed by '
          'drift\nuntil the block space outgrows the budget; a deleterious valley '
          'collapses\nsuccess at a far smaller width. The barrier is the valley, not '
          'the parts.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
