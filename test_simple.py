import unittest

import mutated_simple


class TestHelloWorld(unittest.TestCase):
    def test_return(self):
        self.assertEqual('Hello World!', mutated_simple.hello_world())


if __name__ == '__main__':
    unittest.main()
