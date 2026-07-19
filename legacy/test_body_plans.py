import unittest

import mutated_body_plans


class TestBodyPlans(unittest.TestCase):
    def test_description(self):
        multi_body = mutated_body_plans.MultiBody()
        self.assertTrue(multi_body.description in ('Animal-Body plan 1',
                                                   'Animal-Body plan 2',
                                                   'Animal-Body plan 3',
                                                   'Animal-Body plan 4',
                                                   'Animal-Body plan 5',
                                                   'Animal-Body plan 6',
                                                   'Animal-Body plan 7',
                                                   'Animal-Body plan 8',
                                                   'Animal-Body plan 9'))


if __name__ == '__main__':
    unittest.main()
