"""Tests for the tunable fitness landscape.

Written before the implementation.

The landscape exists to separate two things that the "747" argument keeps
fusing: the number of parts a target has, and the size of the no-benefit gap
that must be crossed to reach it. A genome is N binary parts, the target is
all-correct, and the coordination degree g controls how many of those parts pay
off only when all of them are correct at once.

  g = 1  : every part is independently rewarded. A pure ridge, climbable one
           step at a time.
  g = N  : nothing is rewarded until the whole thing is complete. An isolated
           island, reachable only by getting all N right at once.
"""

import unittest

from ridge import landscape


class TestStructure(unittest.TestCase):

    def test_all_broken_scores_zero(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=2)
        self.assertEqual(0, land.fitness((0, 0, 0, 0, 0, 0)))

    def test_all_correct_is_the_maximum(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=2)
        self.assertEqual(land.max_fitness, land.fitness((1, 1, 1, 1, 1, 1)))
        self.assertEqual(6, land.max_fitness)

    def test_each_reducible_part_adds_fitness(self):
        """The first N-g parts form the ridge: each correct one helps on its own."""
        land = landscape.Landscape(n_parts=6, coordination_degree=2)
        self.assertEqual(1, land.fitness((1, 0, 0, 0, 0, 0)))
        self.assertEqual(2, land.fitness((1, 1, 0, 0, 0, 0)))
        self.assertEqual(4, land.fitness((1, 1, 1, 1, 0, 0)))

    def test_a_neutral_gap_pays_nothing_until_complete(self):
        """With valley_depth 0 a partial block is worth the same as an empty one:
        a flat gap that drift can wander across."""
        land = landscape.Landscape(n_parts=6, coordination_degree=2, valley_depth=0)
        empty = (1, 1, 1, 1, 0, 0)
        one_block_bit = (1, 1, 1, 1, 1, 0)
        self.assertEqual(land.fitness(empty), land.fitness(one_block_bit))

    def test_a_valley_penalises_every_partial_step(self):
        """With valley_depth > 0 each block part added lowers fitness: selection
        actively opposes crossing."""
        land = landscape.Landscape(n_parts=6, coordination_degree=3, valley_depth=2)
        empty = (1, 1, 1, 0, 0, 0)
        one = (1, 1, 1, 1, 0, 0)
        two = (1, 1, 1, 1, 1, 0)
        self.assertEqual(3, land.fitness(empty))
        self.assertEqual(1, land.fitness(one), 'first block part should cost 2')
        self.assertEqual(-1, land.fitness(two), 'second block part should cost 2 more')

    def test_completing_a_valley_still_reaches_the_summit(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=3, valley_depth=2)
        self.assertEqual(land.max_fitness, land.fitness((1, 1, 1, 1, 1, 1)))

    def test_completing_the_block_pays_the_whole_bonus_at_once(self):
        land = landscape.Landscape(n_parts=6, coordination_degree=2)
        before = land.fitness((1, 1, 1, 1, 1, 0))
        after = land.fitness((1, 1, 1, 1, 1, 1))
        self.assertEqual(2, after - before, 'the block bonus should equal g')

    def test_the_plateau_sits_g_below_the_summit(self):
        """A population climbs the ridge to here, then must cross the gap."""
        land = landscape.Landscape(n_parts=10, coordination_degree=3)
        plateau = (1, 1, 1, 1, 1, 1, 1, 0, 0, 0)
        self.assertEqual(land.max_fitness - 3, land.fitness(plateau))


class TestTheTwoExtremes(unittest.TestCase):

    def test_coordination_one_is_a_pure_ridge(self):
        """Every single part is independently rewarded: no gap anywhere."""
        land = landscape.Landscape(n_parts=8, coordination_degree=1)
        for correct in range(9):
            genome = tuple([1] * correct + [0] * (8 - correct))
            self.assertEqual(correct, land.fitness(genome))

    def test_coordination_n_is_all_or_nothing(self):
        """Nothing is rewarded until the whole target is complete."""
        land = landscape.Landscape(n_parts=8, coordination_degree=8)
        self.assertEqual(0, land.fitness((1, 1, 1, 1, 1, 1, 1, 0)))
        self.assertEqual(8, land.fitness((1, 1, 1, 1, 1, 1, 1, 1)))


class TestValidation(unittest.TestCase):

    def test_coordination_cannot_exceed_parts(self):
        with self.assertRaises(ValueError):
            landscape.Landscape(n_parts=4, coordination_degree=5)

    def test_coordination_must_be_at_least_one(self):
        with self.assertRaises(ValueError):
            landscape.Landscape(n_parts=4, coordination_degree=0)

    def test_is_optimal_recognises_the_summit(self):
        land = landscape.Landscape(n_parts=5, coordination_degree=2)
        self.assertTrue(land.is_optimal((1, 1, 1, 1, 1)))
        self.assertFalse(land.is_optimal((1, 1, 1, 1, 0)))

    def test_wrong_length_genome_is_rejected(self):
        land = landscape.Landscape(n_parts=5, coordination_degree=2)
        with self.assertRaises(ValueError):
            land.fitness((1, 1, 1))


if __name__ == '__main__':
    unittest.main()
