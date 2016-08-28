import unittest
import subprocess

import mutated_english
import mutate


class TestEnglish(unittest.TestCase):
    def test_return(self):
        self.assertTrue(mutate.spelled_correctly(mutated_english.quote))
        self.assertEqual(0, subprocess.call(['pylint', 'mutated_hello_world_tested.py']))


if __name__ == '__main__':
    unittest.main()
