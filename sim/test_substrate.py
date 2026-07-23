"""Tests for the mutable Python-program substrate."""

import unittest

from sim import substrate

# A minimal program that accepts the full call and returns a valid decision.
FUNCTIONAL = ('def act(age, fuel, max_fuel, food_available, population):\n'
              '    return {"eat": 1, "reproduce": False, "endowment": 0}\n')


class TestFunctionality(unittest.TestCase):

    def test_the_ancestor_is_functional(self):
        self.assertTrue(substrate.is_functional(substrate.ANCESTOR))

    def test_a_minimal_valid_program_is_functional(self):
        self.assertTrue(substrate.is_functional(FUNCTIONAL))

    def test_a_syntax_error_is_not_functional(self):
        self.assertFalse(substrate.is_functional('def act('))

    def test_missing_act_is_not_functional(self):
        self.assertFalse(substrate.is_functional('x = 1'))

    def test_wrong_arity_is_not_functional(self):
        # decide() calls act with five arguments; a one-argument act raises.
        self.assertFalse(substrate.is_functional('def act(age):\n    return 1\n'))


class TestBehaviour(unittest.TestCase):

    def test_evaluate_is_none_for_a_broken_program(self):
        self.assertIsNone(substrate.evaluate('def act('))

    def test_evaluate_covers_every_context(self):
        fingerprint = substrate.evaluate(FUNCTIONAL)
        self.assertIsNotNone(fingerprint)
        self.assertEqual(len(substrate.CONTEXTS), len(fingerprint))

    def test_the_same_source_has_the_same_fingerprint(self):
        self.assertEqual(substrate.evaluate(FUNCTIONAL), substrate.evaluate(FUNCTIONAL))

    def test_changed_behaviour_gives_a_different_fingerprint(self):
        other = FUNCTIONAL.replace('"eat": 1', '"eat": 2')
        self.assertNotEqual(substrate.evaluate(FUNCTIONAL), substrate.evaluate(other))


class TestMutation(unittest.TestCase):

    def test_a_seed_is_deterministic(self):
        self.assertEqual(substrate.mutate_once(substrate.ANCESTOR, 7),
                         substrate.mutate_once(substrate.ANCESTOR, 7))

    def test_returns_source_text(self):
        self.assertIsInstance(substrate.mutate_once(substrate.ANCESTOR, 1), str)


if __name__ == '__main__':
    unittest.main()
