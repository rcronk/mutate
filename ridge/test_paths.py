"""Tests for accessible-path analysis.

Written before the implementation.

This is the bridge from Part A to real data. Part A asked, dynamically, whether
selection can cross a gap. This asks the same thing structurally: between a
starting genotype and a target that differ at k positions, does a path exist
that flips those k positions one at a time without fitness ever going *down*?

  - A path that never decreases is crossable: selection climbs the uphill parts
    and drift wanders the flat parts. Ridges and neutral gaps qualify.
  - A path that must go down to get up is a valley. That is the barrier Part A
    identified, and here it shows up as zero accessible paths.

The same analyzer runs on Part A's synthetic landscapes and on a real protein
landscape, because both are just a fitness value attached to each genotype. That
is Weinreich's method (2006), and it is how Part B will measure real data.
"""

import unittest

from ridge import landscape, paths


class TestOnHandBuiltLandscapes(unittest.TestCase):

    def test_a_strictly_uphill_pair_has_one_accessible_path_each_way(self):
        # k=2. 00 -> 11. Both single steps up, both doubles up: both orders work.
        fitness = {(0, 0): 0, (1, 0): 1, (0, 1): 1, (1, 1): 2}.get
        result = paths.accessible_paths(fitness, k=2)
        self.assertEqual(2, result.total)
        self.assertEqual(2, result.accessible)

    def test_a_valley_blocks_every_path(self):
        # Both intermediates are worse than the start: a valley.
        fitness = {(0, 0): 5, (1, 0): 1, (0, 1): 1, (1, 1): 10}.get
        result = paths.accessible_paths(fitness, k=2)
        self.assertEqual(0, result.accessible)

    def test_one_good_intermediate_leaves_one_path(self):
        # 00->10->11 is uphill; 00->01->11 dips at 01.
        fitness = {(0, 0): 0, (1, 0): 1, (0, 1): -1, (1, 1): 2}.get
        result = paths.accessible_paths(fitness, k=2)
        self.assertEqual(1, result.accessible)
        self.assertEqual(2, result.total)

    def test_a_flat_intermediate_is_accessible_non_strictly(self):
        # Neutral step: fitness does not rise but does not fall. Crossable by drift.
        fitness = {(0, 0): 0, (1, 0): 0, (0, 1): 0, (1, 1): 1}.get
        result = paths.accessible_paths(fitness, k=2)
        self.assertEqual(2, result.accessible, 'flat steps should count as accessible')


class TestValleyDepth(unittest.TestCase):

    def test_no_valley_when_a_path_is_accessible(self):
        fitness = {(0, 0): 0, (1, 0): 1, (0, 1): 1, (1, 1): 2}.get
        self.assertEqual(0, paths.min_valley_depth(fitness, k=2))

    def test_reports_the_shallowest_required_dip(self):
        # Best path dips by 1 (through the -1 intermediate); the other dips more.
        fitness = {(0, 0): 0, (1, 0): -1, (0, 1): -4, (1, 1): 2}.get
        self.assertEqual(1, paths.min_valley_depth(fitness, k=2))


class TestOnPartALandscapes(unittest.TestCase):
    """The unification: run Part B's analyzer on Part A's landscapes and get
    answers consistent with Part A's dynamics."""

    @staticmethod
    def _fitness_over_block(land):
        """Fixes the reducible ridge as solved and varies only the block, so the
        genotype is the k-bit block and fitness is the landscape's score."""
        reducible_solved = tuple([1] * land.reducible)
        return lambda block: land.fitness(reducible_solved + tuple(block))

    def test_a_ridge_is_fully_accessible(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=4, valley_depth=0)
        result = paths.accessible_paths(self._fitness_over_block(land), k=4)
        self.assertEqual(result.total, result.accessible,
                         'a neutral block should have every path accessible')

    def test_a_valley_is_inaccessible(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=4, valley_depth=2)
        result = paths.accessible_paths(self._fitness_over_block(land), k=4)
        self.assertEqual(0, result.accessible,
                         'a deleterious block should have no accessible path')

    def test_valley_depth_matches_the_dial(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=3, valley_depth=2)
        # Crossing the 3-wide block dips by valley_depth per step; the shallowest
        # forced dip is the single deepest step down, which is valley_depth.
        self.assertEqual(2, paths.min_valley_depth(self._fitness_over_block(land), k=3))


class TestLargerSpaces(unittest.TestCase):

    def test_exact_enumeration_for_small_k(self):
        land = landscape.Landscape(n_parts=8, coordination_degree=5, valley_depth=0)
        reducible = tuple([1] * land.reducible)
        result = paths.accessible_paths(lambda b: land.fitness(reducible + tuple(b)), k=5)
        self.assertEqual(120, result.total, '5! direct paths expected')

    def test_sampling_for_large_k_reports_it(self):
        land = landscape.Landscape(n_parts=14, coordination_degree=11, valley_depth=0)
        reducible = tuple([1] * land.reducible)
        result = paths.accessible_paths(lambda b: land.fitness(reducible + tuple(b)),
                                        k=11, max_exact=8, samples=500)
        self.assertTrue(result.sampled)
        self.assertEqual(500, result.total)

    def test_small_k_is_not_sampled(self):
        fitness = {(0, 0): 0, (1, 0): 1, (0, 1): 1, (1, 1): 2}.get
        self.assertFalse(paths.accessible_paths(fitness, k=2).sampled)


if __name__ == '__main__':
    unittest.main()
