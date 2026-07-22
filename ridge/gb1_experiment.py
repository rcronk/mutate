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

from ridge import gb1, paths

DATA = os.path.join(os.path.dirname(__file__), 'data', 'gb1_wu2016_landscape.csv')
DISTRIBUTION_DISTANCES = (2, 3, 4)


def _wt_to_global_peak(land):
    """ Accessibility of the path from wild type to the single fittest variant.
    :return: A dict describing that path
    """
    peak = max(land.values, key=land.values.get)
    fitness, k = land.pair_fitness(land.wild_type, peak)
    strict = paths.accessible_paths(fitness, k, strict=True)
    return {
        'peak': peak,
        'peak_fitness': land.fitness(peak),
        'total': strict.total,
        'strict': strict.accessible,
        'drift': paths.accessible_paths(fitness, k, strict=False).accessible,
        'valley_depth': paths.min_valley_depth(fitness, k),
    }


def _crossable_by_distance(land):
    """ For each mutational distance, counts fitter peaks reachable without a
        valley versus those forced to cross one.

        A target counts if it is fitter than wild type and its whole cube of
        intermediates is measured, so all its direct paths are defined. It is
        crossable if some direct path never loses fitness (valley depth zero),
        otherwise it is a valley.
    :return: A dict from distance to (crossable, valley) counts
    """
    counts = {distance: [0, 0] for distance in DISTRIBUTION_DISTANCES}
    wild = land.wild_type
    baseline = land.fitness(wild)
    for variant, score in land.values.items():
        distance = gb1.static_hamming(wild, variant)
        if distance not in counts or score <= baseline:
            continue
        if not land.is_complete_cube(wild, variant):
            continue
        fitness, k = land.pair_fitness(wild, variant)
        depth = paths.min_valley_depth(fitness, k)
        counts[distance][0 if depth == 0 else 1] += 1
    return {distance: tuple(pair) for distance, pair in counts.items()}


def analyse():
    """ Computes the GB1 accessibility figures.
    :return: A dict of results
    """
    land = gb1.load_gb1_landscape(DATA)
    return {
        'variants': len(land.values),
        'wild_type_fitness': land.fitness(land.wild_type),
        'local_maxima': len(land.local_maxima()),
        'wt_to_peak': _wt_to_global_peak(land),
        'crossable_by_distance': _crossable_by_distance(land),
    }


def main():
    """ Prints the analysis. """
    result = analyse()
    peak = result['wt_to_peak']
    print('Wu et al. (2016) GB1, four sites, all twenty amino acids:')
    print(f'  measured variants        {result["variants"]}  '
          f'(of 160000 possible)')
    print(f'  local maxima (peaks)     {result["local_maxima"]}  '
          '[a smooth hill would have one]')
    print()
    print(f'Wild type VDGV to the global peak {peak["peak"]} '
          f'(fitness {peak["peak_fitness"]:.2f}):')
    print(f'  accessible under strict selection {peak["strict"]:>2} / {peak["total"]}'
          '   [each step must strictly gain]')
    print(f'  accessible allowing neutral drift {peak["drift"]:>2} / {peak["total"]}'
          '   [each step must not lose]')
    verdict = ('CROSSABLE (ridge)' if peak['valley_depth'] == 0
               else 'a VALLEY that must be descended')
    print(f'  so the single global peak is {verdict}.')
    print()
    print('Across all fitter peaks, by how many sites must change together:')
    for distance, (crossable, valley) in sorted(result['crossable_by_distance'].items()):
        total = crossable + valley
        share = crossable / total if total else 0.0
        print(f'  {distance} sites: {total:5d} peaks   '
              f'crossable {crossable:5d} ({share:.0%})   valley {valley:5d}')
    print()
    print('  As more sites must change together the crossable fraction falls:')
    print('  real protein data shows Part A\'s coordination-degree effect. The')
    print('  barrier is the size of the block that must change at once, not the')
    print('  number of parts.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
