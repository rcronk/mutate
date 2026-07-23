"""Tests for the single-creature performance assay.

The pinned integer scores follow from the fixed world and lifecycle parameters,
so they are a deterministic regression. The behaviours they encode are the
point: a program that crashes, never eats, or never breeds scores low or zero,
and a program that feeds and breeds every fertile tick scores at the ceiling.
"""

import unittest

from sim import life, substrate


def _program(eat, reproduce, endowment):
    return (f'def act(age, fuel, max_fuel, food_available, population):\n'
            f'    return {{"eat": {eat}, "reproduce": {reproduce}, '
            f'"endowment": {endowment}}}\n')


class TestReproductiveOutput(unittest.TestCase):

    def test_the_ancestor_reproduces(self):
        self.assertEqual(15, life.reproductive_output(substrate.ANCESTOR))

    def test_an_unparseable_program_scores_zero(self):
        self.assertEqual(0, life.reproductive_output('def act('))

    def test_a_crashing_program_scores_zero(self):
        crashes = ('def act(age, fuel, max_fuel, food_available, population):\n'
                   '    return 1 / 0\n')
        self.assertEqual(0, life.reproductive_output(crashes))

    def test_a_program_that_never_breeds_scores_zero(self):
        self.assertEqual(0, life.reproductive_output(_program(6, False, 0)))

    def test_a_greedy_breeder_hits_the_fertile_window_ceiling(self):
        # Fertile ages 2..30 inclusive is 29 ticks, so 29 births is the maximum.
        self.assertEqual(29, life.reproductive_output(_program(40, True, 0)))

    def test_feeding_and_breeding_beats_the_ancestor(self):
        greedy = life.reproductive_output(_program(40, True, 0))
        self.assertGreater(greedy, life.reproductive_output(substrate.ANCESTOR))

    def test_starvation_lowers_output(self):
        # With no food at all, even a would-be breeder starves early.
        starved = life.reproductive_output(_program(40, True, 0),
                                           regrowth=0, starting_food=0)
        fed = life.reproductive_output(_program(40, True, 0))
        self.assertLess(starved, fed)

    def test_is_deterministic(self):
        self.assertEqual(life.reproductive_output(substrate.ANCESTOR),
                         life.reproductive_output(substrate.ANCESTOR))


if __name__ == '__main__':
    unittest.main()
