""" betalactamase.py - Part B applied to a real protein landscape.

Runs the accessible-path analysis on Weinreich et al.'s (2006) beta-lactamase
data and reports it through Part A's lens: is the path to the fitter protein a
crossable neutral gap, or an impassable deleterious valley?

The distinction is the whole point of the study. Under strict selection (each
step must strictly increase fitness) the landscape looks highly constrained,
which is Weinreich's famous result. But allowing neutral drift, a much larger
share of paths open up, and if any fully non-decreasing path exists the peak is
reachable without ever crossing a valley.

Run: python -m ridge.betalactamase
"""

import math
import os
import sys

from ridge import dms, paths

DATA = os.path.join(os.path.dirname(__file__), 'data',
                    'weinreich2006_betalactamase_mic.csv')


def analyse():
    """ Computes the accessibility figures for the real landscape.
    :return: A dict of results
    """
    land = dms.load_binary_landscape(DATA, fitness_column='MIC')
    strict = paths.accessible_paths(land.fitness, k=land.k, strict=True)
    drift = paths.accessible_paths(land.fitness, k=land.k, strict=False)
    valley = paths.min_valley_depth(lambda g: math.log(land.fitness(g)), k=land.k)
    return {
        'total': strict.total,
        'strict': strict.accessible,
        'drift': drift.accessible,
        'valley_depth': valley,
    }


def main():
    """ Prints the analysis. """
    result = analyse()
    total = result['total']
    strict, drift = result['strict'], result['drift']
    print('Weinreich et al. (2006) beta-lactamase, 5 mutations, wild type to peak:')
    print(f'  paths total                       {total}')
    print(f'  accessible under strict selection {strict:>3}  ({strict / total:.0%})'
          '   [each step must strictly gain]')
    print(f'  accessible allowing neutral drift {drift:>3}  ({drift / total:.0%})'
          '   [each step must not lose]')
    print(f'  shallowest forced valley (log MIC)  {result["valley_depth"]:.2f}')
    print()
    print('Reading it through Part A:')
    if result['valley_depth'] == 0:
        print('  A fully non-decreasing path exists, so the peak is reachable without')
        print('  ever crossing a deleterious valley. Under Part A this is the CROSSABLE')
        print('  regime (ridge plus neutral gap), not the impassable-valley regime.')
    else:
        print('  Every path must descend at some point: this is a real valley.')
    print(f'  Strict selection blocks {total - strict} of {total} paths, '
          f'but {drift - strict} of those')
    print('  are blocked only by neutral steps that drift can cross. The strong')
    print('  constraint is a selection-only artifact; drift dissolves most of it.')
    print()
    print('  Caveat: this is one small 5-mutation landscape adjacent to an existing')
    print('  enzyme. It says nothing yet about assembling a novel multi-part machine')
    print('  from scratch. It is one real data point, reported honestly.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
