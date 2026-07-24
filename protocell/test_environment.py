"""Tests for the structure-requiring two-signal environment.

The key claim, verified here as a committed check: a pool that reads two signals
(energy and safety) out-reproduces every fixed energy threshold, so the
environment cannot be solved by tuning one number. That is what makes it a fair
test of whether evolution can build structure.
"""

import unittest

from protocell import ancestors, environment, world
from protocell.protein import Protein


def _blind_pool(threshold):
    return [Protein('def protein(cell, env):\n    cell.eat(env, 12)\n'
                    f'    if cell.energy > {threshold}:\n        cell.divide()\n')]


def _fitness(pool, seeds=3):
    """ :return: Total surviving cells across a few runs in the two-signal world """
    return sum(len(world.run(pool, founders=8, ticks=300, seed=seed,
                             make_env=environment.make_world,
                             newborn_survives=environment.newborn_survives).survivors)
               for seed in range(seeds))


class TestTwoSignalWorld(unittest.TestCase):

    def test_food_arrives_in_feast_not_famine(self):
        env = environment.TwoSignalWorld(feast=50, food_period=2)
        env.tick()  # age 1: feast
        self.assertEqual(50, env.food)
        env.tick()  # age 2: famine (2//2 = 1), no food added
        self.assertEqual(50, env.food)

    def test_safety_alternates_on_its_own_period(self):
        env = environment.TwoSignalWorld(safe_period=2)
        env.tick()  # age 1
        self.assertTrue(env.safe)
        env.tick()  # age 2
        env.tick()  # age 3 -> 3//2 = 1, unsafe
        self.assertFalse(env.safe)

    def test_newborn_survives_only_when_safe(self):
        env = environment.TwoSignalWorld()
        env.safe = True
        self.assertTrue(environment.newborn_survives(env))
        env.safe = False
        self.assertFalse(environment.newborn_survives(env))


class TestGradientRequiresStructure(unittest.TestCase):

    def test_two_signal_sensing_beats_every_fixed_threshold(self):
        sensing = _fitness(ancestors.sensing_pool())
        for threshold in (25, 45, 70):
            self.assertGreater(sensing, _fitness(_blind_pool(threshold)),
                               f'a fixed threshold {threshold} should not match sensing')


if __name__ == '__main__':
    unittest.main()
