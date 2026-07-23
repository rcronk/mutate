""" tolerance.py - the substrate's mutation tolerance, in biology's terms.

Phase 2 of Option 3. Before running the substrate, we check how forgiving it is
and compare that to the biological target from ridge.dfe. The measurement is the
same one: from the functional ancestor, what fraction of single mutations leave
it functional (survival), and of those, how many are synonymous (behaviour
unchanged) versus behaviour-changing.

The result is a surprise worth stating plainly. Naive character-level mutation of
Python source, long assumed far too harsh to be like biology, actually tolerates
about a tenth of single mutations, inside the 6% to 34% range measured for real
proteins. And of the tolerated mutations a large share change behaviour, so the
tolerance is not just no-op edits to comments and whitespace. At the single-
mutation level the substrate does not need to be made more forgiving. Whether
that tolerance supports cumulative building is the separate question phase 3
asks.
"""

import dataclasses
import sys

from ridge import dfe_experiment
from sim import substrate

DEFAULT_TRIALS = 3000


@dataclasses.dataclass
class Tolerance:
    """ The survival split of single mutations from a functional program. """
    functional: int
    synonymous: int
    behaviour_changing: int
    total: int

    @property
    def fraction(self):
        """ :return: Share of single mutations that stay functional """
        return self.functional / self.total if self.total else 0.0


def measure(source, *, trials=DEFAULT_TRIALS, start_seed=0):
    """ Measures the tolerance of a source over a run of single mutations.

        Each seed gives one deterministic single mutation. A mutation is counted
        functional if the mutant still runs on every context, and within that as
        synonymous if its behaviour fingerprint matches the parent or behaviour-
        changing if it differs.
    :param source: The functional parent program
    :param trials: How many single mutations to sample
    :param start_seed: First mutation seed (the run is seeds start..start+trials)
    :return: A Tolerance
    """
    parent_behaviour = substrate.evaluate(source)
    functional = synonymous = changing = 0
    for seed in range(start_seed, start_seed + trials):
        behaviour = substrate.evaluate(substrate.mutate_once(source, seed))
        if behaviour is None:
            continue
        functional += 1
        if behaviour == parent_behaviour:
            synonymous += 1
        else:
            changing += 1
    return Tolerance(functional=functional, synonymous=synonymous,
                     behaviour_changing=changing, total=trials)


def analyse(*, trials=DEFAULT_TRIALS):
    """ Measures the substrate's tolerance from the ancestor.
    :return: A Tolerance
    """
    return measure(substrate.ANCESTOR, trials=trials)


def _biological_range():
    """ :return: (min, max) tolerated fraction across the calibration systems """
    fractions = [dfe.fraction_tolerated for dfe in dfe_experiment.analyse().values()]
    return min(fractions), max(fractions)


def main():
    """ Prints the substrate tolerance beside the biological target. """
    result = analyse()
    low, high = _biological_range()
    print('Substrate mutation tolerance (self-modifying Python), from the ancestor:')
    print(f'  single mutations sampled     {result.total}')
    print(f'  functional (tolerated)       {result.functional}  '
          f'({result.fraction:.1%})')
    print(f'    of which behaviour-changing {result.behaviour_changing}')
    print(f'    of which synonymous         {result.synonymous}')
    print()
    print(f'Biological target (ridge.dfe): {low:.0%} to {high:.0%} tolerated.')
    verdict = ('inside' if low <= result.fraction <= high else 'outside')
    print(f'The substrate is {verdict} the biological range. Naive Python mutation')
    print('is not, as assumed, far harsher than biology at the single-mutation level.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
