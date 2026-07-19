import mutated_beak

import unittest


class TestMultipleFunctions(unittest.TestCase):

    def test_get_beak_length(self):
        self.assertGreaterEqual(9, mutated_beak.get_beak_length())


if __name__ == '__main__':
    unittest.main()
