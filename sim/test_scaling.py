"""Tests for the resource scaling result.

Two claims, and the second corrects the first sweep's premature conclusion.
Below a resource threshold evolution stalls (fast to show here). But with enough
resource it crosses the barrier, proven cheaply by a saved evolved genome that
independently scores far past it, and by the recorded large-scale sweep.
"""

import unittest

from sim import competition, life, scaling


class TestBelowThreshold(unittest.TestCase):

    def test_small_resources_stall_below_the_optimum(self):
        result = scaling.sweep([(10, 10), (20, 20)], seeds=2)
        for scores in result.values():
            self.assertTrue(all(score < scaling.optimum() for score in scores))

    def test_the_control_reaches_its_optimum(self):
        result = scaling.sweep([(10, 10)], seeds=2, fitness=life.reproductive_output)
        self.assertTrue(all(score > scaling.optimum() for score in result[(10, 10)]))

    def test_sweep_is_deterministic(self):
        self.assertEqual(scaling.sweep([(15, 15)], seeds=2),
                         scaling.sweep([(15, 15)], seeds=2))


class TestBarrierIsCrossed(unittest.TestCase):
    """The correction. With enough resource evolution crosses the barrier, shown
    without a slow rerun by the saved genome and the recorded sweep."""

    def test_the_saved_evolved_genome_crosses_the_barrier(self):
        score = competition.competitive_fitness(scaling.crossing_genome())
        self.assertEqual(17, score)
        self.assertGreater(score, scaling.optimum())

    def test_recorded_sweep_crosses_only_at_scale(self):
        crossed = {budget: count for budget, _, count in scaling.RECORDED_RESOURCE_SCALING}
        self.assertEqual(0, crossed[10000])
        self.assertGreater(crossed[640000], 0)

    def test_recorded_mutation_sweep_shows_error_catastrophe(self):
        best = {rate: value for rate, value, _ in scaling.RECORDED_MUTATION_SWEEP}
        self.assertGreater(best[0.3], 0)
        self.assertEqual(0, best[0.9])


if __name__ == '__main__':
    unittest.main()
