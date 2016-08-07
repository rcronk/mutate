import unittest

import mutated_hello_world_tested


class TestHelloWorld(unittest.TestCase):
    def test_return(self):
        self.assertEqual('Hello World!', mutated_hello_world_tested.hello_world())


if __name__ == '__main__':
    unittest.main()
