""" run.py - watch a protocell population live, and read its genome.

Slice 1: no mutation yet, just proof that a pool of stochastically-called
functions runs a living, dividing cell, and that a pool too poor to feed itself
dies. The whole "genome" is printed as source, so you can see exactly what the
cell is, not just a number.

Run: python -m protocell.run
"""

import sys

from protocell import ancestors, world


def main():
    """ Prints a working run and a minimal (dying) run. """
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
    return 0


if __name__ == '__main__':
    sys.exit(main())
