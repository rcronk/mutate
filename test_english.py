import unittest
import subprocess

import mutated_english
import mutate


class TestEnglish(unittest.TestCase):
    def test_return(self):
        self.assertTrue(mutate.Dictionary().spelled_correctly(mutated_english.QUOTE))
        self.assertEqual(0, subprocess.call(['pylint', 'mutated_english.py']))


if __name__ == '__main__':
    unittest.main()
