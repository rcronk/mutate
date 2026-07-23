"""Tests for the TrpB enzyme landscape.

The four-site path mechanics are proven in test_gb1.py and test_four_site.py, so
this pins the TrpB-specific facts: the parent enzyme's residues, the ruggedness,
and the barrier. TrpB is the sharpest case so far, its global peak is a valley
that no direct path reaches, matching the source paper's finding that directed
evolution cannot climb to the optimum.
"""

import os
import tempfile
import unittest

from ridge import trpb, trpb_experiment

DATA = os.path.join(os.path.dirname(__file__), 'data',
                    'johnston2024_trpb_landscape.csv')


class TestLoader(unittest.TestCase):

    def test_sets_the_trpb_parent_as_wild_type(self):
        descriptor, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(descriptor, 'w') as handle:
            handle.write('variant,fitness\nVFVS,0.4\nAAAA,0.1\n')
        self.addCleanup(os.unlink, path)
        land = trpb.load_trpb_landscape(path)
        self.assertEqual('VFVS', land.wild_type)
        self.assertEqual(0.4, land.fitness('VFVS'))


class TestRealLandscape(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.land = trpb.load_trpb_landscape(DATA)

    def test_loads_every_measured_standard_variant(self):
        self.assertEqual(159129, len(self.land.values))

    def test_parent_enzyme_is_functional(self):
        self.assertAlmostEqual(0.408, self.land.fitness('VFVS'), places=3)

    def test_the_global_peak_is_aikg(self):
        peak = max(self.land.values, key=self.land.values.get)
        self.assertEqual('AIKG', peak)
        self.assertAlmostEqual(1.0, self.land.fitness(peak), places=3)

    def test_the_landscape_is_very_rugged(self):
        self.assertEqual(802, len(self.land.local_maxima()))


class TestOptimisationBarrier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = trpb_experiment.analyse()

    def test_the_global_peak_is_a_valley_no_direct_path_reaches(self):
        peak = self.result['wt_to_peak']
        self.assertEqual(24, peak['total'])
        self.assertEqual(0, peak['strict'])
        self.assertEqual(0, peak['drift'])
        self.assertGreater(peak['valley_depth'], 0)

    def test_crossable_by_distance_is_pinned(self):
        self.assertEqual({2: (33, 71), 3: (63, 386), 4: (12, 518)},
                         self.result['crossable_by_distance'])

    def test_crossable_fraction_falls_as_coordination_grows(self):
        counts = self.result['crossable_by_distance']
        fraction = {d: c / (c + v) for d, (c, v) in counts.items()}
        self.assertGreater(fraction[2], fraction[3])
        self.assertGreater(fraction[3], fraction[4])


if __name__ == '__main__':
    unittest.main()
