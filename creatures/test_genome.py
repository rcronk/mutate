"""Tests for the creature genome: source text, mutation, and lineage seeding.

Written before the implementation.

Three things are pinned here.

A creature is Python source holding only its decision behavior. The lifecycle
rules live in the engine (see lifecycle.py) where mutation cannot reach them.

Mutants are checked with ast.parse before anything is spawned, so a syntax
error costs a parse rather than a process. Semantic errors still survive the
gate and kill the creature at runtime, which is the interesting part.

A child's seed derives from its parent's seed and birth index, so the same
creature always produces the same offspring. Process scheduling is
nondeterministic but genetics are not, which is what makes a lineage
reproducible.
"""

import ast
import unittest

from creatures import genome


class TestAncestor(unittest.TestCase):

    def test_ancestor_is_valid_python(self):
        ast.parse(genome.ANCESTOR_SOURCE)

    def test_ancestor_exposes_an_act_function(self):
        loaded = genome.load(genome.ANCESTOR_SOURCE)
        self.assertTrue(callable(loaded))

    DECISION_KEYS = ('eat', 'reproduce', 'endowment')

    def decide(self, **overrides):
        """Run the ancestor with default senses, overriding as needed."""
        args = {'age': 1, 'fuel': 5, 'max_fuel': 20,
                'food_available': 100, 'population': 10}
        args.update(overrides)
        return genome.decide(genome.ANCESTOR_SOURCE, **args)

    def test_ancestor_returns_a_full_decision(self):
        decision = self.decide()
        for key in self.DECISION_KEYS:
            self.assertIn(key, decision)

    def test_ancestor_eats_when_low_on_fuel(self):
        self.assertGreater(self.decide(fuel=1)['eat'], 0)

    def test_ancestor_eats_harder_when_food_is_scarce(self):
        """A strategy that is only possible now that the creature can see the
        pool and the population."""
        plenty = self.decide(fuel=18, food_available=1000, population=5)
        scarce = self.decide(fuel=18, food_available=2, population=50)
        self.assertGreater(scarce['eat'], plenty['eat'])

    def test_ancestor_asks_to_breed_when_healthy(self):
        self.assertTrue(self.decide(age=3, fuel=20)['reproduce'])

    def test_ancestor_does_not_ask_to_breed_when_starving(self):
        self.assertFalse(self.decide(age=3, fuel=1)['reproduce'])

    def test_ancestor_endows_its_offspring(self):
        """Offspring investment is the evolvable life-history dial."""
        self.assertGreater(self.decide(fuel=20)['endowment'], 0)

    def test_a_poorer_parent_endows_less(self):
        self.assertGreater(self.decide(fuel=40, max_fuel=40)['endowment'],
                           self.decide(fuel=8, max_fuel=40)['endowment'])

    def test_ancestor_does_not_police_its_own_fertility(self):
        """It asks at every age; lifecycle.can_reproduce decides. An earlier
        ancestor hardcoded `2 <= age <= 5`, which capped every creature at two
        breeding attempts no matter what the engine allowed and drove every
        population extinct."""
        self.assertTrue(self.decide(age=0, fuel=20)['reproduce'])
        self.assertTrue(self.decide(age=99, fuel=20)['reproduce'])


class TestDecisionNormalising(unittest.TestCase):
    """A mutant can return nonsense. The engine must never trust it."""

    ARGS = {'age': 1, 'fuel': 5, 'max_fuel': 20, 'food_available': 100, 'population': 10}
    SIG = 'def act(age, fuel, max_fuel, food_available, population):'

    def decide(self, body):
        """Run a one-line act() body against fixed senses."""
        return genome.decide(f'{self.SIG}\n    {body}\n', **self.ARGS)

    def test_missing_keys_get_defaults(self):
        decision = self.decide('return {}')
        self.assertEqual(0, decision['eat'])
        self.assertFalse(decision['reproduce'])
        self.assertEqual(0, decision['endowment'])

    def test_negative_eat_is_clamped_to_zero(self):
        self.assertEqual(0, self.decide('return {"eat": -50}')['eat'])

    def test_absurd_eat_is_clamped_to_max_fuel(self):
        self.assertEqual(20, self.decide('return {"eat": 10 ** 9}')['eat'])

    def test_non_numeric_eat_becomes_zero(self):
        self.assertEqual(0, self.decide('return {"eat": "lots"}')['eat'])

    def test_negative_endowment_is_clamped_to_zero(self):
        self.assertEqual(0, self.decide('return {"endowment": -5}')['endowment'])

    def test_endowment_is_capped(self):
        """A creature cannot conjure fuel to give away that it does not have."""
        self.assertLessEqual(self.decide('return {"endowment": 10 ** 9}')['endowment'],
                             self.ARGS['max_fuel'])

    def test_non_numeric_endowment_becomes_zero(self):
        self.assertEqual(0, self.decide('return {"endowment": None}')['endowment'])

    def test_non_dict_return_is_rejected(self):
        with self.assertRaises(genome.MisbehavingCreatureError):
            self.decide('return 42')

    def test_raising_creature_is_reported_not_propagated(self):
        with self.assertRaises(genome.MisbehavingCreatureError):
            self.decide('raise ValueError("boom")')

    def test_wrong_arity_is_misbehaving(self):
        """Mutation deletes arguments. A creature that no longer accepts the
        full call is misbehaving and dies in the world, as before."""
        with self.assertRaises(genome.MisbehavingCreatureError):
            genome.decide('def act(only_one_arg):\n    return {}\n', **self.ARGS)

    def test_missing_act_is_rejected(self):
        with self.assertRaises(genome.MisbehavingCreatureError):
            genome.decide('x = 1\n', **self.ARGS)


class TestSyntaxGate(unittest.TestCase):
    """Invalid mutants must be rejected before anything is spawned."""

    def test_valid_source_passes(self):
        self.assertTrue(genome.is_viable(genome.ANCESTOR_SOURCE))

    def test_syntax_error_fails(self):
        self.assertFalse(genome.is_viable('def act(age, fuel, max_fuel)\n  return {}'))

    def test_empty_source_fails(self):
        self.assertFalse(genome.is_viable(''))

    def test_source_without_act_fails(self):
        self.assertFalse(genome.is_viable('x = 1\n'))

    def test_gate_never_raises_on_arbitrary_bytes(self):
        for junk in ('%%%', '\x00\x01', 'def :', 'return', '}{'):
            with self.subTest(junk=junk):
                self.assertFalse(genome.is_viable(junk))


class TestMutation(unittest.TestCase):

    def test_mutation_changes_the_source(self):
        mutated = genome.mutate_source(genome.ANCESTOR_SOURCE, seed=1)
        self.assertNotEqual(genome.ANCESTOR_SOURCE, mutated)

    def test_same_seed_gives_the_same_mutant(self):
        self.assertEqual(genome.mutate_source(genome.ANCESTOR_SOURCE, seed=7),
                         genome.mutate_source(genome.ANCESTOR_SOURCE, seed=7))

    def test_different_seeds_give_different_mutants(self):
        self.assertNotEqual(genome.mutate_source(genome.ANCESTOR_SOURCE, seed=1),
                            genome.mutate_source(genome.ANCESTOR_SOURCE, seed=2))

    def test_most_mutants_are_rejected_by_the_gate(self):
        """Python source is brittle. This is the honest baseline: the vast
        majority of single mutations do not survive parsing."""
        viable = sum(genome.is_viable(genome.mutate_source(genome.ANCESTOR_SOURCE, seed=s))
                     for s in range(300))
        self.assertLess(viable, 250, 'suspiciously tolerant')
        self.assertGreater(viable, 0, 'nothing survives, so nothing can ever evolve')

    def test_low_mutation_rate_does_not_bias_the_operator(self):
        """The mutate-or-not coin and the mutation must use independent seeds.
        Reusing one seed forced every low-probability mutation to be a prepend,
        which made 97% of mutants unparseable and nearly froze evolution. The
        parse rate among actual mutations must not depend on the rate."""
        founder = genome.Genome.founder(seed=42)
        mutated = attempts = 0
        for i in range(3000):
            child = founder.child(birth_index=i, mutation_probability=0.1)
            if child is None:
                attempts += 1
            elif child.source != genome.ANCESTOR_SOURCE:
                attempts += 1
                mutated += 1
        parse_rate = mutated / attempts
        self.assertGreater(parse_rate, 0.2,
                           f'only {parse_rate:.0%} of mutations parsed; the coin and '
                           f'the mutation are probably sharing a seed again')


class TestLineage(unittest.TestCase):
    """Genetics are reproducible even though process timing is not."""

    @staticmethod
    def first_viable_child(parent, start=0):
        """Births can fail, so find one that did not. Which indices succeed is
        itself deterministic, so this is stable across runs."""
        for index in range(start, start + 500):
            child = parent.child(birth_index=index)
            if child is not None:
                return index, child
        raise AssertionError('no viable child in 500 attempts')

    def test_founder_has_generation_one(self):
        founder = genome.Genome.founder(seed=42)
        self.assertEqual(1, founder.generation)
        self.assertEqual('0', founder.identity)

    def test_founders_can_be_given_distinct_identities(self):
        """Several founders sharing identity '0' made every lineage in the
        event log look like it descended from one creature."""
        identities = {genome.Genome.founder(seed=i, identity=str(i)).identity
                      for i in range(5)}
        self.assertEqual(5, len(identities))

    def test_child_seed_derives_from_parent_and_birth_index(self):
        founder = genome.Genome.founder(seed=42)
        first_index, first = self.first_viable_child(founder)
        _, second = self.first_viable_child(founder, start=first_index + 1)
        self.assertNotEqual(first.seed, second.seed)

    def test_same_parent_and_index_always_gives_the_same_child(self):
        index, first = self.first_viable_child(genome.Genome.founder(seed=42))
        second = genome.Genome.founder(seed=42).child(birth_index=index)
        self.assertEqual(first.seed, second.seed)
        self.assertEqual(first.source, second.source)
        self.assertEqual(first.identity, second.identity)

    def test_different_founder_seeds_give_different_lineages(self):
        _, first = self.first_viable_child(genome.Genome.founder(seed=1))
        _, second = self.first_viable_child(genome.Genome.founder(seed=2))
        self.assertNotEqual(first.seed, second.seed)

    def test_generation_increments_down_the_lineage(self):
        creature = genome.Genome.founder(seed=42)
        for _ in range(4):
            _, creature = self.first_viable_child(creature)
        self.assertEqual(5, creature.generation)

    def test_identity_records_ancestry(self):
        founder = genome.Genome.founder(seed=42)
        child_index, child = self.first_viable_child(founder)
        grandchild_index, grandchild = self.first_viable_child(child)
        self.assertEqual('0', founder.identity)
        self.assertEqual(f'0.{child_index}', child.identity)
        self.assertEqual(f'0.{child_index}.{grandchild_index}', grandchild.identity)

    def test_a_lineage_replays_identically(self):
        """The whole point: rerun the same founder seed and get byte-identical
        genomes back, including which births failed."""
        def walk():
            creature = genome.Genome.founder(seed=99)
            path = []
            for _ in range(4):
                _, creature = self.first_viable_child(creature)
                path.append(creature.source)
            return path

        self.assertEqual(walk(), walk())

    def test_child_source_is_a_mutant_of_the_parent(self):
        founder = genome.Genome.founder(seed=42)
        child = next(c for c in (founder.child(birth_index=i) for i in range(200))
                     if c is not None)
        self.assertNotEqual(founder.source, child.source)

    def test_a_birth_can_fail(self):
        """Exactly one mutation is attempted per birth. Most fail to parse, and
        a failed birth produces no offspring rather than being retried."""
        founder = genome.Genome.founder(seed=42)
        outcomes = [founder.child(birth_index=i) for i in range(200)]
        failures = [o for o in outcomes if o is None]
        successes = [o for o in outcomes if o is not None]
        self.assertGreater(len(failures), 0, 'no birth ever failed, so the gate does nothing')
        self.assertGreater(len(successes), 0, 'no birth ever succeeded, so nothing can evolve')

    def test_a_failed_birth_is_reproducible(self):
        """Whether a given birth fails is part of the genetics, not chance."""
        first = genome.Genome.founder(seed=42).child(birth_index=5)
        second = genome.Genome.founder(seed=42).child(birth_index=5)
        self.assertEqual(first is None, second is None)

    def test_surviving_children_always_parse(self):
        """The gate's only job: nothing unparseable is ever handed back, so no
        process is ever forked for something that cannot even be read."""
        founder = genome.Genome.founder(seed=42)
        for index in range(50):
            child = founder.child(birth_index=index)
            if child is not None:
                with self.subTest(index=index):
                    self.assertTrue(genome.is_viable(child.source))

    def test_parsing_is_not_the_same_as_working(self):
        """Roughly half of mutants that parse still crash when called. Those
        must reach the world and die there, so the cause is recorded, rather
        than being filtered out here."""
        founder = genome.Genome.founder(seed=1)
        broken = 0
        for index in range(300):
            child = founder.child(birth_index=index)
            if child is None:
                continue
            try:
                genome.decide(child.source, age=3, fuel=5, max_fuel=20,
                              food_available=100, population=10)
            except genome.MisbehavingCreatureError:
                broken += 1
        self.assertGreater(broken, 0,
                           'the gate is filtering out runtime failures it should not')


if __name__ == '__main__':
    unittest.main()
