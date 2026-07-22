"""Tests for the ancestral steroid-receptor landscape and its origin-of-new-
function analysis.

The loader is checked on a tiny hand-written table where every field is visible.
The recognition-helix landscape has the same four-site shape as GB1, so the path
mechanics are already proven in test_gb1.py and are not retested here. What is
pinned on the real data is the scientific payload: reaching the new SRE function
needs coordinated change and gets harder with it, and every helix that gains SRE
has given up the ancestral ERE function.
"""

import os
import tempfile
import unittest

from ridge import steroid, steroid_experiment

DATA = os.path.join(os.path.dirname(__file__), 'data',
                    'herrera2025_ancSR1_RH.csv.gz')


class TestLoader(unittest.TestCase):

    def _write(self, text):
        descriptor, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def _small(self):
        return self._write(
            'variant,ERE_meanF,ERE_active,SRE_meanF,SRE_active\n'
            'EGKA,1.0,TRUE,0.0,FALSE\n'
            'EGKV,0.5,FALSE,2.0,TRUE\n'
            'XGKA,9.0,TRUE,9.0,TRUE\n')  # non-standard residue X, must be skipped

    def test_reads_both_functions_per_variant(self):
        data = steroid.load_ancsr1(self._small())
        self.assertEqual(1.0, data.ere.fitness('EGKA'))
        self.assertEqual(2.0, data.sre.fitness('EGKV'))

    def test_active_flags_become_sets(self):
        data = steroid.load_ancsr1(self._small())
        self.assertIn('EGKA', data.ere_active)
        self.assertNotIn('EGKA', data.sre_active)  # ancestor lacks the new function
        self.assertIn('EGKV', data.sre_active)

    def test_non_standard_residues_are_skipped(self):
        data = steroid.load_ancsr1(self._small())
        with self.assertRaises(KeyError):
            data.sre.fitness('XGKA')

    def test_missing_ancestor_is_an_error(self):
        with self.assertRaises(ValueError):
            steroid.load_ancsr1(self._small(), ancestral_rh='ZZZZ')


class TestRealLandscape(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = steroid.load_ancsr1(DATA)

    def test_loads_the_full_grid(self):
        self.assertEqual(160000, len(self.data.sre.values))

    def test_ancestor_binds_ere_but_not_sre(self):
        self.assertIn('EGKA', self.data.ere_active)
        self.assertNotIn('EGKA', self.data.sre_active)
        self.assertAlmostEqual(-3.40, self.data.ere.fitness('EGKA'), places=2)
        self.assertAlmostEqual(-4.47, self.data.sre.fitness('EGKA'), places=2)

    def test_the_new_function_is_rare(self):
        self.assertEqual(59, len(self.data.sre_active))


class TestOriginOfNewFunction(unittest.TestCase):
    """The scientific payload, pinned from analyse()."""

    @classmethod
    def setUpClass(cls):
        cls.result = steroid_experiment.analyse()

    def test_new_function_needs_two_to_four_coordinated_changes(self):
        self.assertEqual({2: 1, 3: 20, 4: 38},
                         self.result['sre_active_by_distance'])

    def test_accessibility_on_sre_is_pinned(self):
        self.assertEqual({2: (1, 2, 1), 3: (42, 120, 18), 4: (80, 912, 21)},
                         self.result['sre_accessibility'])

    def test_climbable_fraction_falls_as_coordination_grows(self):
        access = self.result['sre_accessibility']
        strict_fraction = {d: s / t for d, (s, t, _) in access.items()}
        self.assertGreater(strict_fraction[2], strict_fraction[3])
        self.assertGreater(strict_fraction[3], strict_fraction[4])

    def test_gaining_the_new_function_costs_the_old_one(self):
        """The pleiotropic valley: no SRE-active helix keeps ERE above the
        ancestor, so the path to the new function descends on the old."""
        self.assertEqual(0, self.result['sre_active_keeping_ere'])
        self.assertGreater(self.result['ere_drop_min'], 0)


if __name__ == '__main__':
    unittest.main()
