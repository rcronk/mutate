""" Tests for the Wright-Fisher waiting-time engine.

Two kinds of check: the sampler primitives behave, and the whole engine
reproduces the analytic waiting times. The second kind is the point of the
slice, so it is asserted against analytic.py, not against a frozen number.
"""

import random
import unittest

from kaxis import analytic, population


class TestBinomial(unittest.TestCase):

    def test_mean_is_trials_times_probability(self):
        rng = random.Random(0)
        draws = [population._binomial(1000, 0.01, rng) for _ in range(4000)]  # pylint: disable=protected-access
        self.assertAlmostEqual(10.0, sum(draws) / len(draws), delta=0.5)

    def test_degenerate_probabilities(self):
        rng = random.Random(0)
        self.assertEqual(0, population._binomial(1000, 0.0, rng))  # pylint: disable=protected-access
        self.assertEqual(1000, population._binomial(1000, 1.0, rng))  # pylint: disable=protected-access
        self.assertEqual(0, population._binomial(0, 0.5, rng))  # pylint: disable=protected-access


class TestWaitingTime(unittest.TestCase):

    def test_is_deterministic_for_a_seed(self):
        first = population.mean_waiting_time(1000, (1e-4,), replicates=200, seed=3)
        second = population.mean_waiting_time(1000, (1e-4,), replicates=200, seed=3)
        self.assertEqual(first, second)

    def test_one_step_matches_the_exact_analytic_wait(self):
        pop_size, rate = 1000, 3.36e-5
        simulated = population.mean_waiting_time(pop_size, (rate,), replicates=4000, seed=1)
        predicted = analytic.one_step_wait(pop_size, rate)
        self.assertLess(abs(simulated / predicted - 1.0), 0.05)

    def test_two_step_wait_grows_as_the_square_root_not_linearly(self):
        # The discriminating test: cutting u2 by 16 should lengthen the wait by
        # about sqrt(16) = 4 (drift-assisted, Durrett-Schmidt), not by 16 (the
        # naive "both mutations at once" model). A neutral intermediate drifts and
        # gives the second step many extra chances.
        pop_size, rate1 = 1000, 1e-3
        rarer = population.mean_waiting_time(pop_size, (rate1, 8e-6), replicates=150, seed=7)
        common = population.mean_waiting_time(pop_size, (rate1, 128e-6), replicates=150, seed=107)
        ratio = rarer / common
        self.assertGreater(ratio, 2.5)
        self.assertLess(ratio, 7.0)


class TestSelection(unittest.TestCase):

    def test_fixation_fraction_matches_kimura(self):
        # The selection dial: a beneficial mutant fixes at about Kimura's rate.
        selection = 0.05
        simulated = population.fixation_fraction(1000, selection, replicates=1500, seed=0)
        predicted = analytic.fixation_probability(1000, selection)
        self.assertLess(abs(simulated - predicted), 0.02)


if __name__ == '__main__':
    unittest.main()
