import unittest

import mutated_body_plans


class TestBodyPlans(unittest.TestCase):
    def test_description(self):
        multi_body = mutated_body_plans.MultiBody()
        self.assertTrue(multi_body.description in ('Brachiopod', 'Marrella', 'Trilobite', 'Hallucigenia'))


if __name__ == '__main__':
    unittest.main()
