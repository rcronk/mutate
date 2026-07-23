"""Tests for the substrate's mutation tolerance.

The pinned counts depend on the mutation RNG and so are a reproducibility
regression; the claim that matters is that the substrate's single-mutation
tolerance falls inside the biological range measured in ridge.dfe (6% to 34%).
"""

import unittest

from sim import substrate, tolerance


class TestSubstrateTolerance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = tolerance.analyse()

    def test_pinned_counts(self):
        self.assertEqual(3000, self.result.total)
        self.assertEqual(315, self.result.functional)
        self.assertEqual(173, self.result.synonymous)
        self.assertEqual(142, self.result.behaviour_changing)

    def test_functional_splits_into_synonymous_and_changing(self):
        self.assertEqual(self.result.functional,
                         self.result.synonymous + self.result.behaviour_changing)

    def test_tolerance_is_within_the_biological_range(self):
        # ridge.dfe: 6.5% (steroid) to 33.9% (GB1).
        self.assertGreaterEqual(self.result.fraction, 0.06)
        self.assertLessEqual(self.result.fraction, 0.34)

    def test_a_meaningful_share_of_tolerated_mutations_change_behaviour(self):
        # Not just synonymous no-ops: the substrate has explorable variation.
        self.assertGreater(self.result.behaviour_changing, 0)


class TestMeasureIsDeterministic(unittest.TestCase):

    def test_two_short_runs_agree(self):
        first = tolerance.measure(substrate.ANCESTOR, trials=50)
        second = tolerance.measure(substrate.ANCESTOR, trials=50)
        self.assertEqual((first.functional, first.synonymous),
                         (second.functional, second.synonymous))


if __name__ == '__main__':
    unittest.main()
