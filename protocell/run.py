""" run.py - watch a protocell population live, and read its genome.

Slice 1: no mutation yet, just proof that a pool of stochastically-called
functions runs a living, dividing cell, and that a pool too poor to feed itself
dies. The whole "genome" is printed as source, so you can see exactly what the
cell is, not just a number.

Run: python -m protocell.run
"""

import random
import sys

from protocell import ancestors, mutation, world


def _mutating_run():
    """ Runs the crude reproducing pool under mutation, so the effect is visible. """
    rng = random.Random(0)
    result = world.run(ancestors.crude_pool(), founders=15, ticks=400, seed=0,
                       mutate=lambda pool: mutation.mutate(pool, rng))
    print('CRUDE pool WITH mutation (observed spectrum):')
    print(f'  population over time (every 40 ticks): {result.history[::40]}')
    print('  an evolved genome, note the accumulated duplication and junk:')
    for line in result.survivors[0].dump().splitlines():
        print(f'    {line}')


def main():
    """ Prints a working run, a minimal (dying) run, and a mutating run. """
    working = world.run(ancestors.working_pool(), founders=10, ticks=120, seed=0)
    print('WORKING pool: a cell run by a pool of stochastically-called proteins.')
    print(f'  population over time (every 10 ticks): {working.history[::10]}')
    print(f'  survivors: {len(working.survivors)}   divisions: {working.generations}')
    print('  the whole genome of a survivor, readable:')
    for line in working.survivors[0].dump().splitlines():
        print(f'    {line}')
    print()
    minimal = world.run(ancestors.minimal_pool(), founders=10, ticks=120, seed=0)
    print('MINIMAL pool: cannot feed itself.')
    print(f'  population over time (every 10 ticks): {minimal.history[::10]}')
    print(f'  extinct: {minimal.extinct}')
    print()
    _mutating_run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
