import mutated_multiple_functions

import unittest

phrase = 'The quick brown fox jumped over the lazy dog'

class TestMultipleFunctions(unittest.TestCase):

    def test_words(self):
        self.assertEqual(9, mutated_multiple_functions.count_words(phrase))

    def test_letters(self):
        self.assertEqual(36, mutated_multiple_functions.count_letters(phrase))

    def test_spaces(self):
        self.assertEqual(8, mutated_multiple_functions.count_spaces(phrase))

    def test_stats(self):
        stats = mutated_multiple_functions.get_stats(phrase)
        self.assertEqual(9, stats['words'])
        self.assertEqual(36, stats['letters'])
        self.assertEqual(8, stats['spaces'])


if __name__ == '__main__':
    unittest.main()
