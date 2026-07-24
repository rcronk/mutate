"""Tests for the competitive environment and the barrier it exposes.

The competitive world reverses the solo assay's incentives: provisioning and
restraint beat greedy over-production. And it exposes the coordination barrier
from Part A and B inside the simulation: the balanced optimum exists and pays,
but cumulative selection from the ancestor does not reach it with modest
resources.
"""

import unittest

from sim import competition, evolve, substrate


def _program(eat, reproduce, endowment):
    return (f'def act(age, fuel, max_fuel, food_available, population):\n'
            f'    return {{"eat": {eat}, "reproduce": {reproduce}, '
            f'"endowment": {endowment}}}\n')


class TestCompetitiveFitness(unittest.TestCase):

    def test_a_broken_program_scores_zero(self):
        self.assertEqual(0, competition.competitive_fitness('def act('))

    def test_provisioning_and_restraint_beat_greedy(self):
        greedy = competition.competitive_fitness(_program(40, True, 0))
        balanced = competition.competitive_fitness(_program(8, True, 8))
        self.assertGreater(balanced, greedy)

    def test_the_balanced_optimum_is_pinned(self):
        self.assertEqual(7, competition.competitive_fitness(_program(8, True, 8)))

    def test_ancestor_and_greedy_are_both_low(self):
        # 29 greedy births collapse to one survivor; the ancestor fares no better.
        self.assertEqual(1, competition.competitive_fitness(substrate.ANCESTOR))
        self.assertEqual(1, competition.competitive_fitness(_program(40, True, 0)))


class TestEvolutionStallsAtTheBarrier(unittest.TestCase):
    """The coordination barrier inside the simulation. The balanced optimum
    exists and beats the ancestor sevenfold, but reaching it needs coordinated
    changes to several values at once, which single mutations do not make, so
    modest-resource evolution stalls far below it. Whether more resources cross
    the barrier is the scaling-law question."""

    def test_evolution_stalls_below_the_optimum(self):
        optimum = competition.competitive_fitness(_program(8, True, 8))
        result = evolve.run(population_size=40, generations=40, mutation_rate=0.3,
                            seed=0, fitness=competition.competitive_fitness)
        self.assertLess(result.best_score, optimum)


if __name__ == '__main__':
    unittest.main()
