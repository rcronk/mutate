""" Tests for placing real protein data on the K-axis.

The numbers come from the ridge/ analyses of real measured landscapes, so these
check the bridge (the information formula and the regime split) and the one claim
that carries the slice: measured gradient availability declines with K.
"""

import unittest

from kaxis import biology


class TestSpecifiedInformation(unittest.TestCase):

    def test_halving_the_frequency_adds_one_bit(self):
        self.assertAlmostEqual(1.0, biology.specified_information_bits(0.5))

    def test_keefe_szostak_is_about_37_bits(self):
        bits = biology.specified_information_bits(biology.KEEFE_SZOSTAK_FREQUENCY)
        self.assertAlmostEqual(37.0, bits, delta=1.0)


class TestRealLandscapes(unittest.TestCase):

    def test_gradient_availability_declines_with_k(self):
        fractions = [fraction for _, fraction, _ in biology.tuning_gradient_by_k()]
        self.assertEqual(fractions, sorted(fractions, reverse=True))
        self.assertGreater(len(fractions), 1)

    def test_betalactamase_regimes_are_a_partition(self):
        regimes = biology.betalactamase_regimes()
        self.assertAlmostEqual(
            1.0, regimes['gradient'] + regimes['drift_only'] + regimes['valley'])
        self.assertGreater(regimes['drift_only'], 0.0)


if __name__ == '__main__':
    unittest.main()
