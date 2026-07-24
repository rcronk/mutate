"""Tests for the observed-spectrum mutation operators."""

import random
import unittest

from protocell import mutation
from protocell.protein import Protein

SOURCE = 'def protein(cell, env):\n    cell.eat(env, 4)\n'


class TestPointSpectrum(unittest.TestCase):

    def test_point_events_follow_the_observed_shares(self):
        # Substitutions keep length, insertions add one, deletions remove one.
        rng = random.Random(0)
        same = longer = shorter = 0
        for _ in range(3000):
            mutant = mutation._point_mutate(SOURCE, rng)  # pylint: disable=protected-access
            if len(mutant) == len(SOURCE):
                same += 1
            elif len(mutant) == len(SOURCE) + 1:
                longer += 1
            else:
                shorter += 1
        # ~92% substitutions, the rest indels; assert substitution dominance.
        self.assertGreater(same / 3000, 0.85)
        self.assertGreater(longer, 0)
        self.assertGreater(shorter, 0)

    def test_point_mutation_of_empty_source_grows_it(self):
        self.assertEqual(1, len(mutation._point_mutate('', random.Random(0))))  # pylint: disable=protected-access


class TestMutate(unittest.TestCase):

    def _pool(self):
        return [Protein(SOURCE)]

    def test_returns_proteins(self):
        result = mutation.mutate(self._pool(), random.Random(1))
        self.assertTrue(all(isinstance(protein, Protein) for protein in result))

    def test_is_deterministic_for_a_seed(self):
        first = mutation.mutate(self._pool(), random.Random(2))
        second = mutation.mutate(self._pool(), random.Random(2))
        self.assertEqual([p.source for p in first], [p.source for p in second])

    def test_no_events_leaves_the_pool_unchanged(self):
        result = mutation.mutate(self._pool(), random.Random(3), point_lambda=0.0,
                                 duplication_rate=0.0, protein_deletion_rate=0.0)
        self.assertEqual([SOURCE], [p.source for p in result])

    def test_duplication_grows_the_pool(self):
        result = mutation.mutate(self._pool(), random.Random(4), point_lambda=0.0,
                                 duplication_rate=1.0, protein_deletion_rate=0.0)
        self.assertEqual(2, len(result))

    def test_protein_deletion_shrinks_the_pool(self):
        pool = [Protein(SOURCE), Protein(SOURCE)]
        result = mutation.mutate(pool, random.Random(5), point_lambda=0.0,
                                 duplication_rate=0.0, protein_deletion_rate=1.0)
        self.assertEqual(1, len(result))


if __name__ == '__main__':
    unittest.main()
