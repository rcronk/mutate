""" paths.py - accessible-path analysis over a genotype landscape.

Between a start genotype and a target that differ at k positions, there are k!
"direct" paths that flip those positions one at a time. A path is *accessible*
if fitness never decreases along it: selection climbs the uphill steps and drift
crosses the flat ones, so an accessible path is one cumulative selection can
traverse. A landscape with no accessible path from start to target is a valley,
which Part A showed is the real barrier.

This is Weinreich et al.'s method (2006). The point of putting it here is that it
runs unchanged on Part A's synthetic landscapes and on a real protein's measured
landscape, because both are just a fitness value attached to each genotype. Part
B uses it to ask where real biology falls on the neutral-to-deleterious axis.

Genotypes here are tuples of k bits, where bit i means "mutation i is present."
Start is all-zero, target is all-one, exactly as in Part A. For real data the k
bits are the k mutations separating a chosen ancestor from a chosen peak, and
the fitness callable looks up the measured value.
"""

import dataclasses
import itertools
import math
import random

# Above this many positions, k! is too large to enumerate, so orderings are
# sampled instead. 8! is 40320, still cheap; 12! is half a billion.
DEFAULT_MAX_EXACT = 8
DEFAULT_SAMPLES = 2000


@dataclasses.dataclass
class PathResult:
    """ The outcome of analysing the paths between two genotypes. """
    accessible: int
    total: int
    sampled: bool

    @property
    def fraction(self):
        """ :return: Fraction of examined paths that are accessible """
        return self.accessible / self.total if self.total else 0.0


def _orderings(k, max_exact, samples, rng):
    """ Yields orderings of the k positions, exactly or by sampling.
    :return: (iterable of orderings, total count, sampled flag)
    """
    if k <= max_exact:
        return list(itertools.permutations(range(k))), math.factorial(k), False
    positions = list(range(k))
    sampled = []
    for _ in range(samples):
        rng.shuffle(positions)
        sampled.append(tuple(positions))
    return sampled, samples, True


def _walk(fitness, ordering):
    """ Walks one path, flipping positions in the given order.
    :return: The fitness at each genotype along the path, start to target
    """
    genotype = [0] * len(ordering)
    scores = [fitness(tuple(genotype))]
    for position in ordering:
        genotype[position] = 1
        scores.append(fitness(tuple(genotype)))
    return scores


def accessible_paths(fitness, k, *, max_exact=DEFAULT_MAX_EXACT,
                     samples=DEFAULT_SAMPLES, seed=0):
    """ Counts how many direct paths from all-zero to all-one never decrease.
    :param fitness: Callable from a k-tuple of 0/1 to a number
    :param k: Number of positions separating start and target
    :param max_exact: Enumerate exactly at or below this k, else sample
    :param samples: How many orderings to sample when k is large
    :param seed: Seed for sampling
    :return: A PathResult
    """
    orderings, total, sampled = _orderings(k, max_exact, samples, random.Random(seed))
    accessible = 0
    for ordering in orderings:
        scores = _walk(fitness, ordering)
        if all(later >= earlier for earlier, later in zip(scores, scores[1:])):
            accessible += 1
    return PathResult(accessible=accessible, total=total, sampled=sampled)


def min_valley_depth(fitness, k, *, max_exact=DEFAULT_MAX_EXACT,
                     samples=DEFAULT_SAMPLES, seed=0):
    """ The shallowest valley that must be crossed to reach the target.

        For each path, the depth is the largest single drop in fitness along it.
        The path that minimises that drop is the easiest way across, so its depth
        is what a population is forced to descend. Zero means an accessible path
        exists.
    :return: The minimum required dip, as a non-negative number
    """
    orderings, _, _ = _orderings(k, max_exact, samples, random.Random(seed))
    best = math.inf
    for ordering in orderings:
        scores = _walk(fitness, ordering)
        worst_drop = max((earlier - later
                          for earlier, later in zip(scores, scores[1:])), default=0)
        best = min(best, max(0, worst_drop))
        if best == 0:
            return 0
    return best
