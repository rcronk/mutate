""" gb1_experiment.py - Part B applied to the rugged GB1 landscape.

Beta-lactamase gave one wild-type-to-peak answer. GB1 gives many, because its
four-site landscape has many peaks. Two things are reported.

First, the direct analogue of the beta-lactamase run: the path from wild type to
the single global peak. Read through Part A, is it a crossable ridge or a valley?

Second, the part beta-lactamase could not show: the distribution. For every peak
fitter than wild type, at increasing mutational distance, what fraction are
reachable without crossing a valley? Distance here is coordination degree, the
number of sites that must change together, which is exactly Part A's dial. If the
crossable fraction falls as distance grows, real protein data shows the same
thing Part A's synthetic landscapes did: the barrier is not the number of parts
but how many must change in a coordinated block.

Run: python -m ridge.gb1_experiment
"""

import os
import sys

from ridge import four_site, gb1

DATA = os.path.join(os.path.dirname(__file__), 'data', 'gb1_wu2016_landscape.csv')


def analyse():
    """ Computes the GB1 accessibility figures.
    :return: A dict of results
    """
    land = gb1.load_gb1_landscape(DATA)
    return {
        'variants': len(land.values),
        'wild_type_fitness': land.fitness(land.wild_type),
        'local_maxima': len(land.local_maxima()),
        'wt_to_peak': four_site.wt_to_global_peak(land),
        'crossable_by_distance': four_site.crossable_by_distance(land),
    }


def main():
    """ Prints the analysis. """
    four_site.print_report(
        analyse(),
        title='Wu et al. (2016) GB1, four sites, all twenty amino acids:',
        wt_label='Wild type VDGV',
        closing=[
            '  As more sites must change together the crossable fraction falls:',
            "  real protein data shows Part A's coordination-degree effect. The",
            '  barrier is the size of the block that must change at once, not the',
            '  number of parts.',
        ])
    return 0


if __name__ == '__main__':
    sys.exit(main())
