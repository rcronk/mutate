"""Tests for the shared four-site accessibility analysis.

Two-character genotypes so every answer is checkable by eye. GB1 and TrpB both
run through this module on real data, so these hand-built cases lock its
behaviour independently of either dataset.
"""

import unittest

from ridge import four_site, gb1


def _land(values):
    return gb1.Gb1Landscape(values=values, wild_type='AA')


class TestGlobalPeak(unittest.TestCase):

    def test_global_peak_is_the_fittest_variant(self):
        land = _land({'AA': 1.0, 'CA': 2.0, 'AC': 3.0, 'CC': 5.0})
        self.assertEqual('CC', four_site.global_peak(land))


class TestWtToGlobalPeak(unittest.TestCase):

    def test_a_smooth_climb_is_crossable(self):
        land = _land({'AA': 1.0, 'CA': 2.0, 'AC': 3.0, 'CC': 5.0})
        result = four_site.wt_to_global_peak(land)
        self.assertEqual('CC', result['peak'])
        self.assertEqual(5.0, result['peak_fitness'])
        self.assertEqual(2, result['total'])
        self.assertEqual(2, result['strict'])
        self.assertEqual(0, result['valley_depth'])

    def test_a_dip_before_the_peak_is_a_valley(self):
        # Both intermediates are below the start, so every path must descend.
        land = _land({'AA': 5.0, 'CA': 1.0, 'AC': 1.0, 'CC': 10.0})
        result = four_site.wt_to_global_peak(land)
        self.assertEqual(0, result['strict'])
        self.assertEqual(0, result['drift'])
        self.assertGreater(result['valley_depth'], 0)


class TestCrossableByDistance(unittest.TestCase):

    def test_counts_a_crossable_distance_two_peak(self):
        land = _land({'AA': 1.0, 'CA': 2.0, 'AC': 3.0, 'CC': 5.0})
        self.assertEqual({2: (1, 0)},
                         four_site.crossable_by_distance(land, distances=(2,)))

    def test_counts_a_valley_distance_two_peak(self):
        land = _land({'AA': 5.0, 'CA': 1.0, 'AC': 1.0, 'CC': 10.0})
        self.assertEqual({2: (0, 1)},
                         four_site.crossable_by_distance(land, distances=(2,)))

    def test_ignores_peaks_no_fitter_than_wild_type(self):
        # CC is not fitter than the AA start, so it is not counted.
        land = _land({'AA': 5.0, 'CA': 1.0, 'AC': 1.0, 'CC': 4.0})
        self.assertEqual({2: (0, 0)},
                         four_site.crossable_by_distance(land, distances=(2,)))


if __name__ == '__main__':
    unittest.main()
