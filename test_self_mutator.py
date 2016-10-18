import unittest
import subprocess
import time

import self_mutator


class TestEnglish(unittest.TestCase):
    def test_stuff(self):
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
        creature.live(9)
        self.assertEqual(0, creature.fuel)
        self.assertFalse(creature.alive)

#    def test_pylint(self):
#        self.assertFalse(subprocess.call(['pylint', 'self_mutator.py']))


if __name__ == '__main__':
    unittest.main()
