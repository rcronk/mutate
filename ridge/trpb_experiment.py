""" trpb_experiment.py - Part B applied to the TrpB enzyme landscape.

The third optimisation landscape, run through exactly the analysis GB1 used, so
the two are directly comparable. The question is the same: is the wild-type-to-
peak path a crossable ridge or a valley, and does the crossable share of fitter
peaks fall as more active-site residues must change together?

TrpB matters here because its published headline is that epistasis and many
local optima keep simulated directed evolution from reaching the global optimum.
That is the coordination-degree barrier stated in an enzyme, and this run puts a
number on it in the same terms as GB1.

Run: python -m ridge.trpb_experiment
"""

import os
import sys

from ridge import four_site, trpb

DATA = os.path.join(os.path.dirname(__file__), 'data',
                    'johnston2024_trpb_landscape.csv')


def analyse():
    """ Computes the TrpB accessibility figures.
    :return: A dict of results
    """
    land = trpb.load_trpb_landscape(DATA)
    return {
        'variants': len(land.values),
        'wild_type': land.wild_type,
        'wild_type_fitness': land.fitness(land.wild_type),
        'local_maxima': len(land.local_maxima()),
        'wt_to_peak': four_site.wt_to_global_peak(land),
        'crossable_by_distance': four_site.crossable_by_distance(land),
    }


def main():
    """ Prints the analysis. """
    result = analyse()
    four_site.print_report(
        result,
        title='Johnston et al. (2024) TrpB, four active-site residues, growth fitness:',
        wt_label=f'Wild type {result["wild_type"]}',
        closing=[
            '  The same coordination-degree effect GB1 showed for a binding protein',
            '  appears in an enzyme: as more active-site residues must change',
            '  together, fewer peaks are reachable without crossing a valley.',
        ])
    return 0


if __name__ == '__main__':
    sys.exit(main())
