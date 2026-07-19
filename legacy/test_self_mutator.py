import unittest
import subprocess
import os

import self_mutator


class TestSelfMutator(unittest.TestCase):
    def test_basic_lifetime(self):
        identity = '1'
        creature = self_mutator.Creature(identity)
        self.assertAlmostEqual(0.0, creature.age, delta=0.1)
        self.assertAlmostEqual(10.0, creature.fuel, delta=0.1)
        self.assertEqual(identity, creature._identity)
        self.assertEqual(1, creature.generation)
        self.assertFalse(creature.can_reproduce)
        self.assertTrue(creature.alive)
        creature.live(1)
        self.assertAlmostEqual(1.0, creature.age, delta=0.1)
        self.assertEqual(9, creature.fuel)
        creature.live(9)  # Warning: This renames the source file.
        self.assertEqual(0, creature.fuel)
        self.assertFalse(creature.alive)

    def test_filename(self):
        identity = '1'
        creature = self_mutator.Creature(identity)
        self.assertEqual('self_mutator.py', os.path.basename(creature.filename))

#    def test_pylint(self):
#        self.assertFalse(subprocess.call(['pylint', 'self_mutator.py']))


if __name__ == '__main__':
    unittest.main()
