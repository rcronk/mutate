""" Tests for the buildability(K) experiment.

The claims are structural and hold on a fast parameter regime: a gradient makes
a K-part structure much cheaper to build, and the cost of removing the gradient
grows as K grows. Deterministic under seeding.
"""

import unittest

from kaxis import buildability

FAST = {'pop_size': 500, 'rate': 5e-4, 'budget': 8000, 'replicates': 60}


def _time(coordination, *, gradient):
    return buildability.build_stats(coordination, gradient=gradient,
                                    seed=100 + coordination, **FAST)[1]


class TestBuildability(unittest.TestCase):

    def test_a_gradient_builds_a_three_part_structure_faster(self):
        no_gradient = _time(3, gradient=False)
        gradient = _time(3, gradient=True)
        self.assertGreater(no_gradient, 2.0 * gradient)

    def test_cost_of_removing_the_gradient_grows_with_k(self):
        ratio_two = _time(2, gradient=False) / _time(2, gradient=True)
        ratio_three = _time(3, gradient=False) / _time(3, gradient=True)
        self.assertGreater(ratio_three, ratio_two)

    def test_is_deterministic_for_a_seed(self):
        first = buildability.build_stats(3, gradient=False, seed=7, **FAST)
        second = buildability.build_stats(3, gradient=False, seed=7, **FAST)
        self.assertEqual(first, second)

    def test_both_regimes_build_within_budget_in_the_fast_regime(self):
        self.assertEqual(1.0, _fraction(3, gradient=False))
        self.assertEqual(1.0, _fraction(3, gradient=True))


def _fraction(coordination, *, gradient):
    return buildability.build_stats(coordination, gradient=gradient,
                                    seed=100 + coordination, **FAST)[0]


if __name__ == '__main__':
    unittest.main()
