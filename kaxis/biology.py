""" biology.py - placing real protein data on the K-axis.

Slice 7. The apparatus (slices 5 and 6) is calibrated and shows that building a
K-part structure is cheap when a gradient of rewarded intermediates exists and
explodes when it does not. That turns the argument into one empirical question:
for real biology, do the intermediates exist and are they rewarded? This module
answers it with measured data instead of assumption, reusing the ridge/ analyses.

The bridge is exact. Weinreich's accessibility criteria map straight onto the
K-axis regimes:

  - STRICT accessible (fitness gains at every step) is the kaxis GRADIENT regime:
    selection climbs a rewarded path, and building is cheap (about linear in K).
  - NON-DECREASING but not strict (crossable only through neutral steps) is the
    kaxis NEUTRAL-INTERMEDIATE regime: drift must carry the flats, which is the
    Durrett-Schmidt square-root law whose cost climbs fast with K.
  - Neither (a forced fitness drop) is a true deleterious valley, harder still.

So a real landscape's accessible-path fractions are a direct measurement of where
it sits between the kaxis regimes. Two ends are anchored:

  - The TUNING end, from deep mutational scans of proteins adjacent to an existing
    enzyme (GB1, beta-lactamase). These measure how much gradient real landscapes
    supply for small K, and how it changes as K grows.
  - The DE NOVO end, from the frequency of a new function in random sequence
    (Keefe and Szostak 2001): about one ATP binder per 10^11 random sequences.
    By I = -log2(F) that is a ~37-bit target found by chance alone, with no
    gradient at all. It sets the scale of the no-gradient end that scans, all
    adjacent to existing function, cannot reach.

Run: python -m kaxis.biology
"""

import math
import sys

from ridge import betalactamase, gb1_experiment

KEEFE_SZOSTAK_FREQUENCY = 1e-11  # ~1 functional ATP binder per 10^11 random sequences


def specified_information_bits(frequency):
    """ :return: I = -log2(frequency), the specified information of a target. """
    return -math.log2(frequency)


def tuning_gradient_by_k():
    """ :return: List of (k, accessible_fraction, targets) from the GB1 scan.

    Accessible here is non-decreasing (drift-allowed), the generous criterion, so
    the decline with k is a lower bound on how fast the pure-gradient share falls.
    """
    gb1 = gb1_experiment.analyse()
    rows = []
    for k, (crossable, valley) in sorted(gb1['crossable_by_distance'].items()):
        total = crossable + valley
        rows.append((k, crossable / total, total))
    return rows


def betalactamase_regimes():
    """ :return: The K=5 beta-lactamase split into the three kaxis regimes. """
    result = betalactamase.analyse()
    total = result['total']
    gradient = result['strict'] / total
    non_decreasing = result['drift'] / total
    return {
        'k': 5,
        'gradient': gradient,
        'drift_only': non_decreasing - gradient,
        'valley': 1.0 - non_decreasing,
    }


def main():
    """ Prints where real protein data sits on the K-axis. """
    print('Placing real protein data on the K-axis.')
    print('The apparatus (slice 6): a gradient of rewarded intermediates makes')
    print('building cheap (about linear in K); without one the cost explodes with')
    print('K. So the question is empirical: how much gradient does biology supply?')
    print()
    print('Tuning end (GB1 scan), accessible (non-decreasing) path share by the')
    print('number of sites that must change together:')
    for k, fraction, targets in tuning_gradient_by_k():
        print(f'  K={k}: {fraction:.0%} of {targets} fitter targets have an accessible path')
    print('  The gradient share falls as K rises: real protein data, not assumption.')
    print()
    regimes = betalactamase_regimes()
    print(f'Beta-lactamase (K={regimes["k"]}), split into the kaxis regimes:')
    print(f'  {regimes["gradient"]:.0%} strict gradient   (cheap, ~linear in K)')
    print(f'  {regimes["drift_only"]:.0%} neutral-drift    (Durrett-Schmidt regime, steep in K)')
    print(f'  {regimes["valley"]:.0%} deleterious valley (harder still)')
    print()
    bits = specified_information_bits(KEEFE_SZOSTAK_FREQUENCY)
    print('De novo end (Keefe and Szostak 2001): about one functional ATP binder')
    print(f'  per 10^11 random sequences, so I = -log2(F) = {bits:.0f} bits found by')
    print('  chance alone, with no gradient. A single simple binder is reachable by')
    print('  luck; coordinated multi-part machines carry far more information, and')
    print('  that is where the no-gradient explosion lives.')
    print()
    print('Honest placement: landscapes adjacent to an existing enzyme sit in the')
    print('buildable, gradient-available regime at low K, which is why tuning is')
    print('observed. But the gradient share declines with K, and scans cannot reach')
    print('the de novo end at all, since every scanned target is next to a working')
    print('enzyme. Where biology\'s large coordinated machines fall between the ends')
    print('is the open question, now bracketed by real numbers instead of assumed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
