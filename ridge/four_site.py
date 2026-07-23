""" four_site.py - accessibility analysis shared by the four-site landscapes.

GB1 and TrpB are both four-site, twenty-amino-acid landscapes carried by a
Gb1Landscape, so the same two questions are asked of each: is the path from the
wild type to the global peak crossable, and how does the crossable share of all
fitter peaks change as more sites must change together. This module holds that
analysis once so gb1_experiment and trpb_experiment do not each reimplement it.
"""

from ridge import gb1, paths

DISTANCES = (2, 3, 4)


def global_peak(land):
    """ :return: The fittest variant in the landscape """
    return max(land.values, key=land.values.get)


def wt_to_global_peak(land):
    """ Accessibility of the path from the wild type to the fittest variant.

        strict counts orderings that gain fitness at every step; drift counts
        orderings that never lose it; valley_depth is the shallowest forced dip,
        zero meaning a never-decreasing path exists.
    :return: A dict describing that path
    """
    peak = global_peak(land)
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


def crossable_by_distance(land, distances=DISTANCES):
    """ For each mutational distance, counts fitter peaks reachable without a
        valley versus those forced to cross one.

        A target counts if it is fitter than the wild type and its whole cube of
        intermediates is measured, so all its direct paths are defined. It is
        crossable if some direct path never loses fitness, otherwise it is a
        valley.
    :param land: A Gb1Landscape
    :param distances: The Hamming distances from the wild type to report
    :return: A dict from distance to (crossable, valley) counts
    """
    counts = {distance: [0, 0] for distance in distances}
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


def print_report(result, *, title, wt_label, closing):
    """ Prints an analyse() result in the shared GB1/TrpB format.
    :param result: A dict with variants, local_maxima, wt_to_peak, and
        crossable_by_distance, as the experiment analyse() functions return
    :param title: The header line naming the dataset
    :param wt_label: How to name the wild type in the peak line
    :param closing: Lines of interpretation, printed after the distribution
    """
    peak = result['wt_to_peak']
    print(title)
    print(f'  measured variants        {result["variants"]}  (of 160000 possible)')
    print(f'  local maxima (peaks)     {result["local_maxima"]}  '
          '[a smooth hill would have one]')
    print()
    print(f'{wt_label} to the global peak {peak["peak"]} '
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
    for line in closing:
        print(line)
