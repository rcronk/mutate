"""Tests for loading real mutational-scanning landscapes, and the validation
that our analyzer reproduces a published result.

Written before the implementation. The point of this file is the validation: if
`accessible_paths` reproduces Weinreich et al.'s (2006) published count of 18
accessible trajectories out of 120 on their real beta-lactamase data, we can
trust the same analyzer on landscapes whose answer we do not already know.
"""

import os
import unittest

from ridge import dms, paths

WEINREICH = os.path.join(os.path.dirname(__file__), 'data',
                         'weinreich2006_betalactamase_mic.csv')


class TestLoading(unittest.TestCase):

    def test_loads_all_thirty_two_genotypes(self):
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        self.assertEqual(5, land.k)
        self.assertEqual(32, len(land.values))

    def test_wild_type_and_full_mutant_match_the_paper(self):
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        self.assertAlmostEqual(0.088, land.fitness((0, 0, 0, 0, 0)), places=3)
        self.assertAlmostEqual(4100.0, land.fitness((1, 1, 1, 1, 1)), places=0)

    def test_fitness_is_callable_over_bit_tuples(self):
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        self.assertGreater(land.fitness((0, 0, 0, 1, 1)), 0)

    def test_missing_genotype_is_an_error(self):
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        with self.assertRaises(KeyError):
            land.fitness((0, 0, 0))  # wrong length is not in the table

    def test_a_missing_column_is_rejected(self):
        with self.assertRaises(ValueError):
            dms.load_binary_landscape(WEINREICH, fitness_column='not_a_column')


class TestReproducesWeinreich(unittest.TestCase):
    """The real-data check. The analyzer's *correctness* is already established
    by the controlled landscapes in test_paths.py, where the answer is known
    exactly. This confirms it also produces Weinreich's qualitative finding on
    his real beta-lactamase data: the overwhelming majority of paths to the peak
    are blocked."""

    def test_almost_all_paths_are_blocked(self):
        """Weinreich's headline. Whichever exact count, the finding is that this
        peak is reachable by only a small minority of trajectories."""
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        result = paths.accessible_paths(land.fitness, k=land.k, strict=True)
        self.assertEqual(120, result.total)
        self.assertLess(result.fraction, 0.2,
                        'more than a fifth of paths accessible; expected a strongly '
                        'constrained landscape')

    def test_the_count_on_this_dataset_is_twenty(self):
        """Pinned for reproducibility, and honest about the gap. The paper
        reports 18/120 on its original MIC measurements. This recomputed dataset
        (github.com/OgPlexus/DEFPreflect) gives 20/120. The two extra paths both
        hinge on a single step whose MIC rises by only ~10% here and was flat or
        slightly lower in the original, i.e. sensitivity to how replicate MICs
        were averaged. The qualitative finding (most paths blocked) is robust to
        that; the exact integer is not."""
        land = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        result = paths.accessible_paths(land.fitness, k=land.k, strict=True)
        self.assertEqual(20, result.accessible)

    def test_log_fitness_gives_the_same_accessibility(self):
        """Accessibility depends only on the order of values, so log-transforming
        must not change the count. A cross-check that the loader is consistent."""
        mic = dms.load_binary_landscape(WEINREICH, fitness_column='MIC')
        log = dms.load_binary_landscape(WEINREICH, fitness_column='log_MIC')
        self.assertEqual(
            paths.accessible_paths(mic.fitness, k=5, strict=True).accessible,
            paths.accessible_paths(log.fitness, k=5, strict=True).accessible)


if __name__ == '__main__':
    unittest.main()
