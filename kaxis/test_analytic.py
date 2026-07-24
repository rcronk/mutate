""" Tests for the closed-form waiting-time referee.

The one-step form is exact; the two-step form is the Durrett-Schmidt
approximation whose signature is the square root on the second rate.
"""

import unittest

from kaxis import analytic


class TestOneStep(unittest.TestCase):

    def test_matches_the_geometric_appearance_probability(self):
        # One survivor, a coin-flip rate: appearance probability 1/2, so wait 2.
        self.assertAlmostEqual(2.0, analytic.one_step_wait(1, 0.5))

    def test_larger_population_waits_less(self):
        self.assertLess(analytic.one_step_wait(1000, 1e-4),
                        analytic.one_step_wait(10, 1e-4))


class TestTwoStep(unittest.TestCase):

    def test_scales_as_the_square_root_of_the_second_rate(self):
        # Cutting u2 by 16 lengthens the wait by sqrt(16) = 4, not by 16.
        base = analytic.two_step_wait(1000, 1e-3, 1.6e-4)
        rarer = analytic.two_step_wait(1000, 1e-3, 1.6e-4 / 16)
        self.assertAlmostEqual(4.0, rarer / base)

    def test_scales_inversely_with_population_and_first_rate(self):
        base = analytic.two_step_wait(1000, 1e-3, 1e-5)
        self.assertAlmostEqual(base / 2.0, analytic.two_step_wait(2000, 1e-3, 1e-5))
        self.assertAlmostEqual(base / 2.0, analytic.two_step_wait(1000, 2e-3, 1e-5))


class TestFixationProbability(unittest.TestCase):

    def test_neutral_mutant_fixes_at_one_over_population(self):
        self.assertAlmostEqual(1.0 / 1000, analytic.fixation_probability(1000, 0.0))

    def test_small_advantage_approaches_haldane_two_s(self):
        # Large population, tiny s: fixation probability is about 2s.
        self.assertAlmostEqual(0.002, analytic.fixation_probability(100000, 0.001), places=5)


if __name__ == '__main__':
    unittest.main()
