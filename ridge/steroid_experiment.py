""" steroid_experiment.py - Part B applied to the origin of a new function.

Beta-lactamase and GB1 asked how an existing function is tuned. This asks the
harder question: from the ancestral recognition helix EGKA, which binds ERE and
is null on SRE, how reachable is SRE, a function that did not exist in this
protein? Two answers are reported.

First, on the new function alone. All the SRE-functional helices sit two to four
substitutions away, so reaching the new function needs coordinated change. As
that number grows, the fraction of paths that climb to it without ever losing
SRE function falls, the same coordination-degree effect Part A dialed by hand
and GB1 showed for optimisation.

Second, the tradeoff optimisation landscapes cannot show. Every SRE-functional
helix has lost the ancestral ERE function. So if selection must keep ERE, every
path to the new function descends a deleterious valley on the old one. That
pleiotropic valley, not the new-function landscape itself, is the real barrier.

Run: python -m ridge.steroid_experiment
"""

import os
import statistics
import sys

from ridge import gb1, paths, steroid

DATA = os.path.join(os.path.dirname(__file__), 'data',
                    'herrera2025_ancSR1_RH.csv.gz')
COORDINATION_DISTANCES = (2, 3, 4)


def _targets_by_distance(data):
    """ Groups the SRE-active helices by their distance from the ancestor.
    :return: A dict from Hamming distance to a list of helices
    """
    groups = {}
    for variant in data.sre_active:
        distance = gb1.static_hamming(data.ancestral_rh, variant)
        groups.setdefault(distance, []).append(variant)
    return groups


def _accessibility_on_sre(data, targets):
    """ Accessibility of the ancestral-to-target paths on the SRE axis.

        strict counts orderings that strictly gain SRE function at every step;
        crossable counts targets reachable by at least one never-losing path.
        With continuous fluorescence the two path criteria coincide, because
        exact ties essentially never occur.
    :return: (strict accessible paths, total paths, crossable targets)
    """
    strict = total = crossable = 0
    for target in targets:
        fitness, k = data.sre.pair_fitness(data.ancestral_rh, target)
        result = paths.accessible_paths(fitness, k, strict=True)
        strict += result.accessible
        total += result.total
        if paths.min_valley_depth(fitness, k) == 0:
            crossable += 1
    return strict, total, crossable


def _ere_cost(data):
    """ How much ancestral ERE function the SRE-active helices give up.
    :return: (count that keep ERE above the ancestor, list of ERE drops)
    """
    ancestral_ere = data.ere.fitness(data.ancestral_rh)
    drops = [ancestral_ere - data.ere.fitness(v) for v in data.sre_active]
    kept = sum(1 for v in data.sre_active
               if data.ere.fitness(v) > ancestral_ere)
    return kept, drops


def analyse():
    """ Computes the origin-of-new-function figures.
    :return: A dict of results
    """
    data = steroid.load_ancsr1(DATA)
    by_distance = _targets_by_distance(data)
    on_sre = {distance: _accessibility_on_sre(data, by_distance.get(distance, []))
              for distance in COORDINATION_DISTANCES}
    kept_ere, ere_drops = _ere_cost(data)
    return {
        'ancestral_rh': data.ancestral_rh,
        'ancestral_ere': data.ere.fitness(data.ancestral_rh),
        'ancestral_sre': data.sre.fitness(data.ancestral_rh),
        'ancestral_is_ere_active': data.ancestral_rh in data.ere_active,
        'ancestral_is_sre_active': data.ancestral_rh in data.sre_active,
        'sre_active_count': len(data.sre_active),
        'sre_active_by_distance': {d: len(v) for d, v in by_distance.items()},
        'sre_accessibility': on_sre,
        'sre_active_keeping_ere': kept_ere,
        'ere_drop_min': min(ere_drops),
        'ere_drop_median': statistics.median(ere_drops),
        'ere_drop_max': max(ere_drops),
    }


def main():
    """ Prints the analysis. """
    result = analyse()
    print('Herrera-Alvarez et al. (2025) AncSR1 recognition helix, origin of')
    print('the derived SRE function:')
    print(f'  ancestral helix {result["ancestral_rh"]}: '
          f'ERE meanF {result["ancestral_ere"]:.2f} '
          f'(active={result["ancestral_is_ere_active"]}), '
          f'SRE meanF {result["ancestral_sre"]:.2f} '
          f'(active={result["ancestral_is_sre_active"]})')
    print(f'  helices with the new SRE function: {result["sre_active_count"]} '
          'of 160000')
    print()
    print('Reaching the new function, on the SRE axis:')
    for distance in COORDINATION_DISTANCES:
        peaks = result['sre_active_by_distance'].get(distance, 0)
        strict, total, crossable = result['sre_accessibility'][distance]
        if not peaks:
            continue
        print(f'  {distance} sites must change: {peaks:2d} peaks   '
              f'strict paths {strict:3d}/{total:<4d} ({strict/total:.0%})   '
              f'crossable peaks {crossable}/{peaks} ({crossable/peaks:.0%})')
    print('  As with GB1, the more sites must change together, the smaller the')
    print('  share of paths that climb without losing the new function.')
    print()
    print('The pleiotropic tradeoff, the real barrier:')
    print(f'  SRE-active helices that keep ERE above the ancestor: '
          f'{result["sre_active_keeping_ere"]} of {result["sre_active_count"]}')
    print(f'  every one gives up ERE function (drop of '
          f'{result["ere_drop_min"]:.2f} to {result["ere_drop_max"]:.2f} meanF, '
          f'median {result["ere_drop_median"]:.2f}).')
    print('  So if selection must keep ERE, the path to the new function is a')
    print('  deleterious valley on the old one. That is the barrier optimisation')
    print('  landscapes never show, and it is specific to originating a new')
    print('  function rather than tuning an existing one.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
