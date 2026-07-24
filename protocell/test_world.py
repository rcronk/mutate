"""Tests for the population run, slice 1's assumption check.

The point of this slice: a pool of stochastically-called functions can host a
living, dividing, competing population, and a pool too poor to feed itself dies.
No mutation yet.
"""

import unittest

from protocell import ancestors, world


class TestWorld(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.working = world.run(ancestors.working_pool(), founders=10,
                                ticks=120, seed=0)

    def test_the_working_pool_sustains_a_population(self):
        self.assertFalse(self.working.extinct)
        self.assertGreater(max(self.working.history), 10)  # it grew past the founders

    def test_the_working_run_is_pinned(self):
        self.assertEqual(44, len(self.working.survivors))
        self.assertEqual(120, self.working.generations)

    def test_a_pool_that_cannot_feed_goes_extinct(self):
        result = world.run(ancestors.minimal_pool(), founders=10, ticks=120, seed=0)
        self.assertTrue(result.extinct)

    def test_a_run_is_deterministic(self):
        first = world.run(ancestors.working_pool(), founders=10, ticks=60, seed=1)
        second = world.run(ancestors.working_pool(), founders=10, ticks=60, seed=1)
        self.assertEqual(first.history, second.history)


if __name__ == '__main__':
    unittest.main()
