"""Tests for the distribution of fitness effects, the simulation's calibration
target.

Correctness is established on a tiny landscape where every step is countable by
hand. The real-data figures are pinned as regression and checked against the
scientific claim: biological forgiveness to single mutations is well below 100%
and well above 0%, and it varies by system.
"""

import unittest

from ridge import dfe, dfe_experiment, gb1


class TestOnAHandBuiltLandscape(unittest.TestCase):
    """Two-character genotypes, wild type AA with fitness 1.0 as the threshold.

    Functional backgrounds (fitness >= 1.0): AA, CA, GA. AC at 0.5 is disruptive
    as a neighbour and never used as a background. Counting every present single
    step by hand gives 6 tolerated, 1 disruptive, 2 beneficial.
    """

    def _land(self):
        return gb1.Gb1Landscape(
            values={'AA': 1.0, 'CA': 2.0, 'AC': 0.5, 'GA': 1.0}, wild_type='AA')

    def test_counts_match_hand_calculation(self):
        result = dfe.measure_landscape(self._land())
        self.assertEqual(6, result.tolerated)
        self.assertEqual(1, result.disruptive)
        self.assertEqual(2, result.beneficial)
        self.assertEqual(7, result.total)

    def test_fractions_match_hand_calculation(self):
        result = dfe.measure_landscape(self._land())
        self.assertAlmostEqual(6 / 7, result.fraction_tolerated)
        self.assertAlmostEqual(1 / 7, result.fraction_disruptive)
        self.assertAlmostEqual(2 / 7, result.fraction_beneficial)

    def test_median_deleterious_effect(self):
        # Tolerated-but-not-beneficial steps have effects [0, 1, 1, 0]; median 0.5.
        self.assertAlmostEqual(0.5, dfe.measure_landscape(self._land())
                               .median_deleterious_effect)

    def test_threshold_can_be_overridden(self):
        # With a threshold of 2.0 only CA is a functional background.
        result = dfe.measure_landscape(self._land(), functional_threshold=2.0)
        # CA's present neighbours AA (1.0) and GA (1.0) are both below 2.0.
        self.assertEqual(0, result.tolerated)
        self.assertEqual(2, result.disruptive)

    def test_empty_when_no_functional_background(self):
        result = dfe.measure_landscape(self._land(), functional_threshold=99.0)
        self.assertEqual(0, result.total)
        self.assertEqual(0.0, result.fraction_tolerated)


class TestCalibrationTarget(unittest.TestCase):
    """The real numbers, pinned, and the claim that matters for Option 3."""

    @classmethod
    def setUpClass(cls):
        cls.results = dfe_experiment.analyse()

    def test_pinned_counts(self):
        gb1_dfe = self.results['GB1 binding']
        self.assertEqual((92216, 179790, 46107), (gb1_dfe.tolerated,
                         gb1_dfe.disruptive, gb1_dfe.beneficial))
        trpb_dfe = self.results['TrpB catalysis']
        self.assertEqual((18542, 64448, 9271), (trpb_dfe.tolerated,
                         trpb_dfe.disruptive, trpb_dfe.beneficial))

    def test_forgiveness_is_between_zero_and_one_everywhere(self):
        for result in self.results.values():
            self.assertGreater(result.fraction_tolerated, 0.0)
            self.assertLess(result.fraction_tolerated, 1.0)

    def test_forgiveness_varies_by_system(self):
        # Binding is more forgiving than catalysis, which is more forgiving than
        # the transcription factor's ancestral function.
        tolerated = {label: r.fraction_tolerated for label, r in self.results.items()}
        self.assertGreater(tolerated['GB1 binding'], tolerated['TrpB catalysis'])
        self.assertGreater(tolerated['TrpB catalysis'],
                           tolerated['steroid receptor, ancestral ERE function'])


if __name__ == '__main__':
    unittest.main()
