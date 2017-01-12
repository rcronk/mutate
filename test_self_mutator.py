import unittest
import os
import subprocess

import self_mutator


class TestSelfMutator(unittest.TestCase):
    def test_basic_lifetime(self):
        identity = '1'
        creature = self_mutator.SelfMutator(identity, 5)
        self.assertEqual(0, creature.age)
        self.assertEqual(self_mutator.SelfMutator.maximum_energy, creature.energy)
        self.assertEqual(identity, creature.identity)
        self.assertEqual(1, creature.generation)
        self.assertFalse(creature.can_reproduce)
        self.assertTrue(creature.alive)
        creature.live(1)
        self.assertEqual(1, creature.age)
        self.assertEqual(9, creature.energy)
        creature.live(self_mutator.SelfMutator.maximum_age)
        self.assertFalse(creature.alive)

    def test_filename(self):
        identity = '1'
        creature = self_mutator.SelfMutator(identity, 5)
        self.assertEqual('self_mutator.py', os.path.basename(creature.filename))

    def test_max_gen_depth(self):
        identity = '1.2.3.4'
        self.assertRaises(Exception, self_mutator.SelfMutator, identity, 3)

    def test_main(self):
        self_mutator.main(['1.2', '--seed', '13', '--maxgen', '3'])

    def test_flawed_copy(self):
        for i in range(1000):
            creature = 'abcdefg'
            result = self_mutator.SelfMutator._flawed_copy(creature)
            if len(result) == len(creature): # overwrite
                pass # an overwrite is usually different, but rarely the same so we can't test
            elif len(result) == len(creature) - 1: # delete
                pass # We deleted something, but we don't know what it was without some inspection
            else:
                if result[:-1] == creature or result[1:] == creature:
                    self.assertNotEqual(result, creature)
                else:
                    self.assertNotEqual(result, creature)

    def test_pylint(self):
        self.assertFalse(subprocess.call(['pylint', 'self_mutator.py']))


if __name__ == '__main__':
    unittest.main()
