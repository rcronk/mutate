import unittest
import os

import self_mutator


class TestSelfMutator(unittest.TestCase):
    def test_basic_lifetime(self):
        identity = '1'
        creature = self_mutator.SelfReplicatingCreature(identity)
        self.assertEqual(0, creature.age)
        self.assertEqual(self_mutator.SelfReplicatingCreature.maximum_energy, creature.energy)
        self.assertEqual(identity, creature.identity)
        self.assertEqual(1, creature.generation)
        self.assertFalse(creature.can_reproduce)
        self.assertTrue(creature.alive)
        creature.live(1)
        self.assertEqual(1, creature.age)
        self.assertEqual(9, creature.energy)
        creature.live(self_mutator.SelfReplicatingCreature.maximum_age)
        self.assertFalse(creature.alive)

    def test_filename(self):
        identity = '1'
        creature = self_mutator.SelfReplicatingCreature(identity)
        self.assertEqual('self_mutator.py', os.path.basename(creature.filename))

    def test_main(self):
        self_mutator.main(['1.2.3.4', '--seed', '13'])

#    def test_pylint(self):
#        self.assertFalse(subprocess.call(['pylint', 'self_mutator.py']))


if __name__ == '__main__':
    unittest.main()
