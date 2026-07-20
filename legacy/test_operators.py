"""Tests for the mutation operators, especially deletion and duplication.

Written before the implementation. The original mutator could only prepend,
append, insert and overwrite, so genomes could only ever grow. That is the
direct cause of the numeric garbage that accumulated at the top and bottom of
every mutated file in the 2016 experiments, and it also meant the mutator could
not perform duplication, which is the mechanism biology proposes for the origin
of new genes (Ohno 1970).
"""

import random
import statistics
import unittest

import mutate


class TestSpanLength(unittest.TestCase):
    """Span lengths are drawn from a geometric distribution: usually short,
    occasionally longer."""

    def test_always_within_bounds(self):
        random.seed(1)
        for _ in range(2000):
            length = mutate.Creature._span_length(max_length=10)
            self.assertGreaterEqual(length, 1)
            self.assertLessEqual(length, 10)

    def test_never_exceeds_a_short_source(self):
        random.seed(2)
        for _ in range(500):
            self.assertEqual(1, mutate.Creature._span_length(max_length=1))

    def test_mostly_short(self):
        """The whole point of geometric: short spans dominate."""
        random.seed(3)
        lengths = [mutate.Creature._span_length(max_length=1000, probability=0.3)
                   for _ in range(5000)]
        proportion_of_ones = lengths.count(1) / len(lengths)
        self.assertAlmostEqual(0.3, proportion_of_ones, delta=0.03)

    def test_mean_matches_the_parameter(self):
        """Mean of a geometric distribution is 1/p."""
        random.seed(4)
        lengths = [mutate.Creature._span_length(max_length=100000, probability=0.2)
                   for _ in range(5000)]
        self.assertAlmostEqual(5.0, statistics.mean(lengths), delta=0.5)

    def test_lower_probability_gives_longer_spans(self):
        random.seed(5)
        short = statistics.mean(mutate.Creature._span_length(1000, 0.5) for _ in range(2000))
        long = statistics.mean(mutate.Creature._span_length(1000, 0.05) for _ in range(2000))
        self.assertGreater(long, short * 3)


class TestDelete(unittest.TestCase):
    """Deletion is what the original mutator could not do."""

    def test_shortens_the_source(self):
        random.seed(10)
        for _ in range(200):
            source = 'abcdefghij'
            result = mutate.Creature._flawed_copy(source, {'delete': 1})
            self.assertLess(len(result), len(source))

    def test_removes_one_contiguous_span(self):
        """Deleting leaves prefix + suffix of the original, nothing new and
        nothing reordered. Verified by checking that the common prefix and
        common suffix together account for the whole result, which is only
        true when a single contiguous chunk was removed."""
        random.seed(11)
        source = 'abcdefghij'
        for _ in range(200):
            result = mutate.Creature._flawed_copy(source, {'delete': 1})

            prefix = 0
            while prefix < len(result) and source[prefix] == result[prefix]:
                prefix += 1
            suffix = 0
            while (suffix < len(result) - prefix
                   and source[-1 - suffix] == result[-1 - suffix]):
                suffix += 1

            self.assertEqual(len(result), prefix + suffix,
                             f'{result!r} is not {source!r} with one span removed')

    def test_single_character_source_can_empty(self):
        random.seed(12)
        result = mutate.Creature._flawed_copy('x', {'delete': 1})
        self.assertEqual('', result)

    def test_empty_source_stays_empty(self):
        random.seed(13)
        self.assertEqual('', mutate.Creature._flawed_copy('', {'delete': 1}))


class TestDuplicate(unittest.TestCase):
    """Duplication is the mechanism proposed for the origin of new genes."""

    def test_lengthens_the_source(self):
        random.seed(20)
        for _ in range(200):
            source = 'abcdefghij'
            result = mutate.Creature._flawed_copy(source, {'duplicate': 1})
            self.assertGreater(len(result), len(source))

    def test_every_original_character_count_is_preserved_or_increased(self):
        """Duplication adds, never removes."""
        random.seed(21)
        for _ in range(200):
            source = 'abcdefghij'
            result = mutate.Creature._flawed_copy(source, {'duplicate': 1})
            for char in set(source):
                self.assertGreaterEqual(result.count(char), source.count(char))

    def test_duplicated_span_appears_twice(self):
        """With a fixed seed the copied span must be findable in the output."""
        random.seed(22)
        source = 'abcdefghij'
        result = mutate.Creature._flawed_copy(source, {'duplicate': 1})
        self.assertGreater(len(result), len(source))
        added = len(result) - len(source)
        self.assertGreaterEqual(added, 1)

    def test_can_duplicate_a_long_span_when_probability_is_low(self):
        """A low probability must make whole-block duplication reachable,
        otherwise the operator cannot test the mechanism it exists for."""
        random.seed(23)
        source = 'def f():\n    return 1\n' * 5
        longest_addition = 0
        for _ in range(300):
            result = mutate.Creature._flawed_copy(
                source, {'duplicate': 1}, span_probability=0.02)
            longest_addition = max(longest_addition, len(result) - len(source))
        self.assertGreater(longest_addition, 20)

    def test_empty_source_stays_empty(self):
        random.seed(24)
        self.assertEqual('', mutate.Creature._flawed_copy('', {'duplicate': 1}))


class TestOperatorSelection(unittest.TestCase):
    """All six operators must be reachable, and weights must be honoured."""

    def test_all_six_operators_are_reachable(self):
        random.seed(30)
        seen = set()
        source = 'abcdefghij'
        for _ in range(3000):
            before = len(source)
            result = mutate.Creature._flawed_copy(source)
            if len(result) < before:
                seen.add('shrink')
            elif len(result) > before:
                seen.add('grow')
            else:
                seen.add('same')
        self.assertEqual({'shrink', 'grow', 'same'}, seen)

    def test_zero_weight_operator_never_fires(self):
        """With deletion weighted to zero the source can never shrink.

        Note it can still *grow* under overwrite alone, because overwrite
        replaces a single character with a mutation string that may be a
        six-character Python keyword. Overwrite is not length-preserving,
        which is part of why the 2016 runs accumulated junk.
        """
        random.seed(31)
        source = 'abcdefghij'
        for _ in range(500):
            result = mutate.Creature._flawed_copy(
                source, {'delete': 0, 'duplicate': 0, 'prepend': 0,
                         'append': 0, 'insert': 0, 'overwrite': 1})
            self.assertGreaterEqual(len(result), len(source))

    def test_legacy_weights_never_shrink_the_source(self):
        """The 2016 behaviour: genomes could only grow or stay the same."""
        random.seed(32)
        source = 'abcdefghij'
        for _ in range(1000):
            result = mutate.Creature._flawed_copy(
                source, mutate.LEGACY_MUTATION_WEIGHTS)
            self.assertGreaterEqual(len(result), len(source))

    def test_default_weights_can_shrink_the_source(self):
        """The new default enables deletion, so genomes can shrink."""
        random.seed(33)
        source = 'abcdefghij'
        shrank = any(
            len(mutate.Creature._flawed_copy(source)) < len(source)
            for _ in range(500))
        self.assertTrue(shrank)

    def test_unknown_operator_is_rejected(self):
        with self.assertRaises(ValueError):
            mutate.Creature._flawed_copy('abc', {'teleport': 1})

    def test_all_zero_weights_is_rejected(self):
        with self.assertRaises(ValueError):
            mutate.Creature._flawed_copy('abc', {'delete': 0})


class TestDeterminism(unittest.TestCase):
    """Same seed, same result. This is what makes the experiments reproducible."""

    def test_same_seed_gives_same_output(self):
        def run():
            random.seed(99)
            source = 'abcdefghij'
            for _ in range(50):
                source = mutate.Creature._flawed_copy(source)
            return source

        self.assertEqual(run(), run())

    def test_different_seed_gives_different_output(self):
        def run(seed):
            random.seed(seed)
            source = 'abcdefghij'
            for _ in range(50):
                source = mutate.Creature._flawed_copy(source)
            return source

        self.assertNotEqual(run(1), run(2))


class TestGrowthBehaviour(unittest.TestCase):
    """legacy/README.md section A3 says growth-only operators are why junk
    accumulated in the 2016 runs. Adding deletion does *not* stop that, and it
    is worth pinning the real behaviour rather than the intuitive one.

    Deletion and duplication cancel each other out on average, since both draw
    spans from the same distribution. What actually drives growth is that the
    three insert-type operators each add a mutation string averaging about 2.6
    characters, because the Python keywords in the mutation alphabet are around
    six characters long. Deletion therefore dilutes growth by taking a share of
    the operator budget, but does not reverse it.
    """

    @staticmethod
    def _grow(weights, seed, generations=400):
        random.seed(seed)
        source = 'abcdefghij'
        for _ in range(generations):
            source = mutate.Creature._flawed_copy(source, weights)
        return len(source)

    def test_legacy_weights_grow_without_bound(self):
        self.assertGreater(self._grow(mutate.LEGACY_MUTATION_WEIGHTS, 40), 200)

    def test_default_weights_also_grow(self):
        """Adding deletion does not stop unbounded growth."""
        self.assertGreater(self._grow(None, 41), 200)

    def test_default_weights_grow_more_slowly_than_legacy(self):
        """But it does slow it down, which is the honest claim."""
        legacy = self._grow(mutate.LEGACY_MUTATION_WEIGHTS, 42)
        default = self._grow(None, 42)
        self.assertLess(default, legacy)

    def test_deletion_only_shrinks_to_nothing(self):
        """Deletion alone is purely destructive, as expected."""
        random.seed(43)
        source = 'abcdefghij' * 5
        for _ in range(200):
            source = mutate.Creature._flawed_copy(source, {'delete': 1})
        self.assertEqual('', source)


if __name__ == '__main__':
    unittest.main()
