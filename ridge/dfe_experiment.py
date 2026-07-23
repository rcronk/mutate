""" dfe_experiment.py - the biological calibration target for the simulation.

Phase one of Option 3. Measures how forgiving real molecules are to single
mutations, across the three landscapes that have a functional wild type
(GB1 binding, TrpB catalysis, and the steroid receptor's ancestral ERE
function). The headline is the tolerated fraction: starting from a working
genotype, how often does a single mutation leave it still working. That number,
not a guess, is what the mutable-Python substrate in the next phase must match.

Run: python -m ridge.dfe_experiment
"""

import os
import sys

from ridge import dfe, gb1, steroid, trpb

DATA = os.path.join(os.path.dirname(__file__), 'data')


def _systems():
    """ :return: A list of (label, landscape) for the functional-wild-type
        landscapes used as calibration targets """
    gb1_land = gb1.load_gb1_landscape(os.path.join(DATA, 'gb1_wu2016_landscape.csv'))
    trpb_land = trpb.load_trpb_landscape(
        os.path.join(DATA, 'johnston2024_trpb_landscape.csv'))
    ancsr1 = steroid.load_ancsr1(os.path.join(DATA, 'herrera2025_ancSR1_RH.csv.gz'))
    return [
        ('GB1 binding', gb1_land),
        ('TrpB catalysis', trpb_land),
        ('steroid receptor, ancestral ERE function', ancsr1.ere),
    ]


def analyse():
    """ Measures the DFE of each calibration system.
    :return: A dict from label to its Dfe
    """
    return {label: dfe.measure_landscape(land) for label, land in _systems()}


def main():
    """ Prints the calibration target. """
    results = analyse()
    print('Biological forgiveness to single mutations, from functional backgrounds:')
    print('(tolerated = the mutant is still at least as fit as the wild type)')
    print()
    for label, result in results.items():
        print(f'  {label}:')
        print(f'    single-mutation steps measured  {result.total}')
        print(f'    tolerated                        {result.fraction_tolerated:6.1%}')
        print(f'    disruptive                       {result.fraction_disruptive:6.1%}')
        print(f'    of which beneficial              {result.fraction_beneficial:6.1%}')
        print()
    tolerated = [r.fraction_tolerated for r in results.values()]
    print(f'Calibration target: a mutable substrate should tolerate roughly '
          f'{min(tolerated):.0%} to {max(tolerated):.0%}')
    print('of single mutations, not ~0% (naive code mutation) and not ~100%. The')
    print('next phase dials the substrate into this range before any scaling runs.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
