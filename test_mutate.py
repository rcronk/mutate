import unittest

import mutate


class TestMutate(unittest.TestCase):
    def test_weighted_choice(self):
        apple = 25
        orange = 15
        grapefruit = 45
        pineapple = 5
        kiwi = 10
        sum = apple + orange + grapefruit + pineapple + kiwi
        iterations = 100000
        choices = [('apple', apple),
                   ('orange', orange),
                   ('grapefruit', grapefruit),
                   ('pineapple', pineapple),
                   ('kiwi', kiwi)]
        results = {}
        for i in range(0, iterations):
            choice = mutate.weighted_choice(choices)
            if choice in results:
                results[choice] += 1
            else:
                results[choice] = 1

        self.assertAlmostEqual(apple / sum, results['apple'] / iterations, 2)
        self.assertAlmostEqual(orange / sum, results['orange'] / iterations, 2)
        self.assertAlmostEqual(grapefruit / sum, results['grapefruit'] / iterations, 2)
        self.assertAlmostEqual(pineapple / sum, results['pineapple'] / iterations, 2)
        self.assertAlmostEqual(kiwi / sum, results['kiwi'] / iterations, 2)

    def test_flawed_copy(self):
        for i in range(1000):
            creature = 'abcdefg'
            result = mutate.flawed_copy(creature)
            if len(result) == len(creature): # overwrite
                pass # an overwrite is usually different, but rarely the same so we can't test anything here
            else:
                if result[:-1] == creature or result[1:] == creature:
                    self.assertNotEqual(result, creature)
                else:
                    self.assertNotEqual(result, creature)

if __name__ == '__main__':
    unittest.main()
