"""Tests for the program-substrate evolutionary loop.

The pinned scores depend on the assay and the mutation RNG, so they are a
reproducibility regression. The claims that matter: the loop is deterministic,
selection raises reproductive output, and with no mutation nothing changes.
"""

import unittest

from sim import evolve, life, substrate


class TestEvolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = evolve.run(population_size=50, generations=40,
                                mutation_rate=0.3, seed=0)

    def test_history_covers_founder_plus_each_generation(self):
        self.assertEqual(41, len(self.result.history))

    def test_starts_at_the_ancestor_score(self):
        self.assertEqual(life.reproductive_output(substrate.ANCESTOR),
                         self.result.history[0])

    def test_selection_raises_reproductive_output(self):
        self.assertGreater(self.result.best_score, self.result.history[0])

    def test_reaches_the_fertile_window_ceiling(self):
        self.assertEqual(29, self.result.best_score)

    def test_is_deterministic(self):
        again = evolve.run(population_size=50, generations=40,
                           mutation_rate=0.3, seed=0)
        self.assertEqual(self.result.history, again.history)
        self.assertEqual(self.result.best_source, again.best_source)


class TestNoMutation(unittest.TestCase):

    def test_without_mutation_nothing_changes(self):
        result = evolve.run(population_size=20, generations=10,
                            mutation_rate=0.0, seed=1)
        self.assertEqual(result.best_source, substrate.ANCESTOR)
        self.assertEqual(set(result.history), {result.history[0]})


if __name__ == '__main__':
    unittest.main()
