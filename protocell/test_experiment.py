"""Tests for the build and degrade experiment.

The results are deterministic (seeded). The build test finds no structure built;
the degrade test finds the structure kept; and the sensing seed carries more
specified information than the blind one, the amount the safety sensor is worth.
Larger, adversarial runs (recorded in the PR) reach the same build result.
"""

import random
import unittest

from protocell import experiment


class TestBuildAndDegrade(unittest.TestCase):

    def test_the_blind_seed_builds_no_safety_sensor(self):
        self.assertEqual([0, 0, 0], experiment.build_test())

    def test_the_sensing_seed_keeps_its_sensor(self):
        self.assertEqual([1.0, 1.0, 1.0], experiment.degrade_test())


class TestSeedInformation(unittest.TestCase):

    def test_sensing_carries_more_specified_information_than_blind(self):
        blind, sensing = experiment.seed_information(random.Random(0), samples=60)
        self.assertGreater(sensing.constrained_sites, blind.constrained_sites)


if __name__ == '__main__':
    unittest.main()
