import unittest
import subprocess
import time

import self_mutator


class TestEnglish(unittest.TestCase):
    def test_stuff(self):
        identity = '1'
        creature = self_mutator.Creature(identity)
        self.assertAlmostEqual(0.0, creature.age, delta=0.1)
        self.assertAlmostEqual(0.0, creature.hunger, delta=0.1)
        self.assertEqual(identity, creature._identity)
        self.assertEqual(1, creature.generation)
        self.assertFalse(creature.can_reproduce)
        self.assertFalse(creature.passed_on)
        # TODO: live(1) instead of sleep?
        time.sleep(1)
        self.assertAlmostEqual(1.0, creature.age, delta=0.1)
        self.assertAlmostEqual(0.0, creature.hunger, delta=0.1)
        # TODO: live(9) instead of sleep?
        time.sleep(9)
        self.assertTrue(creature.passed_on)

#    def test_pylint(self):
#        self.assertFalse(subprocess.call(['pylint', 'self_mutator.py']))


if __name__ == '__main__':
    unittest.main()
