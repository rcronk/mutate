"""Tests for the mutation-selection loop.

Written before the implementation. This is the plainest possible evolutionary
algorithm: a population of binary genomes, tournament selection on fitness, and
per-part mutation. No cleverness, because the point is to show what ordinary
cumulative selection can and cannot do as the landscape's gap changes.
"""

import unittest

from ridge import evolve, landscape


class TestClimbingARidge(unittest.TestCase):
    """With g=1 the whole landscape is a ridge. Selection should walk right up."""

    def test_a_pure_ridge_is_solved(self):
        land = landscape.Landscape(n_parts=12, coordination_degree=1)
        result = evolve.run(land, population_size=50, generations=500,
                            mutation_rate=0.05, seed=1)
        self.assertTrue(result.solved, 'selection failed to climb a pure ridge')

    def test_a_wider_ridge_is_still_solved(self):
        """The headline half: more parts, same tiny gap, still solved. Part
        count is not the barrier."""
        land = landscape.Landscape(n_parts=40, coordination_degree=1)
        result = evolve.run(land, population_size=50, generations=1500,
                            mutation_rate=0.02, seed=1)
        self.assertTrue(result.solved, 'a 40-part ridge should still be climbable')


class TestNeutralGapsAreCrossable(unittest.TestCase):
    """A neutral gap is a flat plateau: drift wanders across it. This is the
    part evolution genuinely does well, and pretending otherwise would be
    dishonest."""

    def test_a_small_neutral_gap_is_crossed(self):
        land = landscape.Landscape(n_parts=12, coordination_degree=2, valley_depth=0)
        result = evolve.run(land, population_size=200, generations=1500,
                            mutation_rate=0.06, seed=1)
        self.assertTrue(result.solved, 'drift should cross a 2-wide neutral gap')

    def test_a_moderate_neutral_gap_is_still_crossed(self):
        """~2^8 block states is a small space to drift through."""
        land = landscape.Landscape(n_parts=12, coordination_degree=8, valley_depth=0)
        result = evolve.run(land, population_size=200, generations=2000,
                            mutation_rate=0.06, seed=1)
        self.assertTrue(result.solved, 'drift should still cross an 8-wide neutral gap')


class TestValleysAreTheBarrier(unittest.TestCase):
    """A deleterious valley is what cumulative selection cannot cross, because
    selection actively pushes back down the slope. This is the real
    irreducible-complexity case."""

    def test_a_wide_valley_is_not_crossed(self):
        """With a valley, drift is useless (selection pushes back), so crossing
        needs all g parts to flip in one leap: cost ~(1/mutation)^g, which is
        out of budget by g=8."""
        land = landscape.Landscape(n_parts=12, coordination_degree=8, valley_depth=3)
        result = evolve.run(land, population_size=200, generations=2000,
                            mutation_rate=0.06, seed=1)
        self.assertFalse(result.solved, 'an 8-wide valley should not be crossed here')

    def test_the_same_gap_flips_from_crossable_to_impassable_with_depth(self):
        """Identical N and g. The only change is whether the intermediates are
        neutral or deleterious, and that alone decides the outcome. This is the
        whole experiment in one comparison."""
        neutral = evolve.run(
            landscape.Landscape(n_parts=12, coordination_degree=8, valley_depth=0),
            population_size=200, generations=2000, mutation_rate=0.06, seed=1)
        valley = evolve.run(
            landscape.Landscape(n_parts=12, coordination_degree=8, valley_depth=3),
            population_size=200, generations=2000, mutation_rate=0.06, seed=1)
        self.assertTrue(neutral.solved, 'the neutral gap should be crossed by drift')
        self.assertFalse(valley.solved, 'the same-width valley should not be crossed')


class TestReporting(unittest.TestCase):

    def test_result_reports_when_it_solved(self):
        land = landscape.Landscape(n_parts=8, coordination_degree=1)
        result = evolve.run(land, population_size=50, generations=500,
                            mutation_rate=0.05, seed=1)
        self.assertIsNotNone(result.solved_at)
        self.assertLessEqual(result.solved_at, 500)

    def test_result_reports_best_fitness_reached(self):
        land = landscape.Landscape(n_parts=8, coordination_degree=8)
        result = evolve.run(land, population_size=50, generations=200,
                            mutation_rate=0.05, seed=1)
        self.assertLessEqual(result.best_fitness, land.max_fitness)

    def test_unsolved_run_has_no_solve_time(self):
        land = landscape.Landscape(n_parts=12, coordination_degree=10)
        result = evolve.run(land, population_size=50, generations=100,
                            mutation_rate=0.05, seed=1)
        if not result.solved:
            self.assertIsNone(result.solved_at)


class TestDeterminism(unittest.TestCase):

    def test_same_seed_same_outcome(self):
        land = landscape.Landscape(n_parts=12, coordination_degree=3)
        first = evolve.run(land, population_size=100, generations=400,
                           mutation_rate=0.05, seed=7)
        second = evolve.run(land, population_size=100, generations=400,
                            mutation_rate=0.05, seed=7)
        self.assertEqual(first.solved_at, second.solved_at)
        self.assertEqual(first.best_fitness, second.best_fitness)

    def test_different_seeds_can_differ(self):
        land = landscape.Landscape(n_parts=12, coordination_degree=4)
        outcomes = {evolve.run(land, population_size=100, generations=800,
                               mutation_rate=0.06, seed=s).solved_at
                    for s in range(8)}
        self.assertGreater(len(outcomes), 1, 'every seed gave the identical time')


if __name__ == '__main__':
    unittest.main()
