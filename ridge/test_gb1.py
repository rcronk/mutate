"""Tests for the GB1 four-site landscape loader and its accessibility analysis.

Two things are checked. First, on small hand-built landscapes, that the loader
and the reduction to binary paths behave exactly as specified: this is where
correctness is established, because the answers are known by inspection. Second,
on the real Wu et al. (2016) data, that the pinned figures reproduce and that
the scientific claim holds: the crossable fraction falls as more sites must
change together, which is Part A's coordination-degree effect in real protein
data.
"""

import os
import unittest

from ridge import gb1, gb1_experiment

DATA = os.path.join(os.path.dirname(__file__), 'data', 'gb1_wu2016_landscape.csv')


class TestOnHandBuiltLandscapes(unittest.TestCase):
    """Two-character genotypes so every answer is checkable by eye."""

    def _square(self):
        # AA -> CC over two sites. All four corners present.
        return gb1.Gb1Landscape(values={'AA': 1.0, 'CA': 2.0, 'AC': 3.0, 'CC': 5.0})

    def test_pair_fitness_maps_bits_to_the_right_genotypes(self):
        fitness, k = self._square().pair_fitness('AA', 'CC')
        self.assertEqual(2, k)
        self.assertEqual(1.0, fitness((0, 0)), 'all-zero is the start')
        self.assertEqual(5.0, fitness((1, 1)), 'all-one is the target')
        self.assertEqual(2.0, fitness((1, 0)), 'first site flipped to target')
        self.assertEqual(3.0, fitness((0, 1)), 'second site flipped to target')

    def test_complete_cube_is_true_when_every_corner_is_present(self):
        self.assertTrue(self._square().is_complete_cube('AA', 'CC'))

    def test_complete_cube_is_false_when_an_intermediate_is_missing(self):
        land = gb1.Gb1Landscape(values={'AA': 1.0, 'CA': 2.0, 'CC': 5.0})  # no AC
        self.assertFalse(land.is_complete_cube('AA', 'CC'))

    def test_pair_fitness_raises_on_a_missing_intermediate(self):
        land = gb1.Gb1Landscape(values={'AA': 1.0, 'CA': 2.0, 'CC': 5.0})  # no AC
        fitness, _ = land.pair_fitness('AA', 'CC')
        with self.assertRaises(KeyError):
            fitness((0, 1))  # asks for the missing AC

    def test_neighbours_are_the_present_single_substitutions(self):
        land = gb1.Gb1Landscape(values={'AA': 1.0, 'CA': 2.0, 'AC': 3.0, 'GG': 9.0})
        # GG differs at two sites, so it is not a neighbour of AA.
        self.assertEqual({'CA', 'AC'}, set(land.neighbours('AA')))

    def test_local_maxima_are_variants_fitter_than_all_neighbours(self):
        self.assertEqual(['CC'], self._square().local_maxima())

    def test_static_hamming_counts_differing_sites(self):
        self.assertEqual(2, gb1.static_hamming('VDGV', 'VDAA'))
        self.assertEqual(0, gb1.static_hamming('VDGV', 'VDGV'))


class TestRealLandscape(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.land = gb1.load_gb1_landscape(DATA)

    def test_loads_every_measured_standard_variant(self):
        self.assertEqual(149361, len(self.land.values))

    def test_wild_type_is_normalised_to_one(self):
        self.assertAlmostEqual(1.0, self.land.fitness('VDGV'))

    def test_an_unmeasured_variant_is_an_error(self):
        with self.assertRaises(KeyError):
            self.land.fitness('ZZZZ')

    def test_a_missing_column_is_rejected(self):
        with self.assertRaises(ValueError):
            gb1.load_gb1_landscape(DATA, fitness_column='not_a_column')

    def test_the_global_peak_is_fwaa(self):
        peak = max(self.land.values, key=self.land.values.get)
        self.assertEqual('FWAA', peak)
        self.assertAlmostEqual(8.76, self.land.fitness(peak), places=2)

    def test_the_landscape_is_rugged(self):
        """Wu et al.'s central finding: far from a single smooth hill."""
        self.assertEqual(182, len(self.land.local_maxima()))


class TestAccessibilityReproducesTheFinding(unittest.TestCase):
    """The scientific payload. analyse() is run once and its numbers checked."""

    @classmethod
    def setUpClass(cls):
        cls.result = gb1_experiment.analyse()

    def test_the_global_peak_is_crossable_like_beta_lactamase(self):
        peak = self.result['wt_to_peak']
        self.assertEqual(24, peak['total'], '4! direct paths')
        self.assertEqual(5, peak['strict'])
        self.assertEqual(0, peak['valley_depth'],
                         'a non-decreasing path exists, so the peak is a ridge')

    def test_crossable_fraction_falls_as_coordination_grows(self):
        """The claim: the more sites must change together, the less often the
        peak is reachable without crossing a valley."""
        counts = self.result['crossable_by_distance']
        fraction = {d: c / (c + v) for d, (c, v) in counts.items()}
        self.assertGreater(fraction[2], fraction[3])
        self.assertGreater(fraction[3], fraction[4])

    def test_distribution_counts_are_pinned(self):
        """Regression pins on the exact (crossable, valley) split per distance."""
        self.assertEqual({2: (86, 112), 3: (186, 1085), 4: (258, 1821)},
                         self.result['crossable_by_distance'])


if __name__ == '__main__':
    unittest.main()
