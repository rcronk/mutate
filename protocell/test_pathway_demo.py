""" Tests for the readable K-axis pathway demo.

The demo illustrates the kaxis result in readable code. These check that the
rendered genome really runs (it is not a picture), that the two chemistries score
as intended, and the one claim it exists to show: a gradient builds a pathway
that stalls without one. A fast, seeded regime keeps it quick and deterministic.
"""

import unittest

from protocell import pathway_demo

FAST = {'pop_size': 150, 'generations': 250, 'trials': 8}


class TestRendering(unittest.TestCase):

    def test_the_rendered_genome_actually_runs(self):
        # Three active enzymes, executed as real proteins, advance the pathway by 3.
        self.assertEqual(3, pathway_demo.working_enzymes(pathway_demo.render_genome({0, 1, 2})))

    def test_a_broken_protein_does_not_count(self):
        genome = pathway_demo.render_genome({0, 1})
        genome.append(pathway_demo.Protein('def protein(cell, env)\n  syntax error'))
        self.assertEqual(2, pathway_demo.working_enzymes(genome))


class TestChemistry(unittest.TestCase):

    def test_gradient_rewards_partial_pathways(self):
        self.assertEqual(2, pathway_demo.fitness({0, 1}, 4, gradient=True))

    def test_no_gradient_rewards_only_the_complete_pathway(self):
        self.assertEqual(0, pathway_demo.fitness({0, 1}, 4, gradient=False))
        self.assertEqual(4, pathway_demo.fitness({0, 1, 2, 3}, 4, gradient=False))


class TestBuildContrast(unittest.TestCase):

    def test_a_gradient_builds_a_pathway_that_stalls_without_one(self):
        with_gradient = pathway_demo.build_fraction(6, gradient=True, **FAST)
        without = pathway_demo.build_fraction(6, gradient=False, **FAST)
        self.assertGreater(with_gradient, 0.5)
        self.assertLess(without, 0.3)

    def test_is_deterministic_for_a_seed(self):
        first = pathway_demo.evolve(5, gradient=True, seed=1)
        second = pathway_demo.evolve(5, gradient=True, seed=1)
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
