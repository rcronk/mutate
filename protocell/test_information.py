"""Tests for the specified-information metric.

Exact per-position counts depend on the sampling RNG, so the tests pin the
metric's *properties*, which are what make it a meaningful measure: a
nonfunctional genome carries no specified information, junk dilutes the
deleterious fraction without adding constrained sites, and the measure is
deterministic for a seed.
"""

import random
import unittest

from protocell import ancestors, information
from protocell.protein import Protein

JUNK = 'def protein(cell, env):\n    a = 111\n    b = a + 222\n'


class TestAssay(unittest.TestCase):

    def test_a_functional_pool_divides(self):
        self.assertGreater(information.assay(ancestors.working_pool()), 0)

    def test_an_inert_pool_does_not_divide(self):
        self.assertEqual(0, information.assay(ancestors.minimal_pool()))


class TestSpecifiedInformation(unittest.TestCase):

    def test_a_functional_pool_has_constrained_sites(self):
        info = information.specified_information(
            ancestors.working_pool(), random.Random(0), samples=120)
        self.assertGreater(info.constrained_sites, 0)
        self.assertGreater(info.deleterious_fraction, 0.7)

    def test_a_nonfunctional_pool_has_no_specified_information(self):
        info = information.specified_information(
            ancestors.minimal_pool(), random.Random(0), samples=60)
        self.assertEqual(0, info.constrained_sites)

    def test_an_empty_pool_is_zero(self):
        info = information.specified_information([], random.Random(0), samples=10)
        self.assertEqual(0, info.constrained_sites)
        self.assertEqual(0, info.genome_length)

    def test_junk_dilutes_the_fraction_but_not_the_constrained_sites(self):
        base = information.specified_information(
            ancestors.working_pool(), random.Random(0), samples=150)
        padded = information.specified_information(
            ancestors.working_pool() + [Protein(JUNK)], random.Random(0), samples=150)
        self.assertLess(padded.deleterious_fraction, base.deleterious_fraction)
        self.assertLess(padded.constrained_sites, base.constrained_sites * 1.3)

    def test_is_deterministic_for_a_seed(self):
        first = information.specified_information(
            ancestors.crude_pool(), random.Random(1), samples=50)
        second = information.specified_information(
            ancestors.crude_pool(), random.Random(1), samples=50)
        self.assertEqual(first.constrained_sites, second.constrained_sites)


if __name__ == '__main__':
    unittest.main()
