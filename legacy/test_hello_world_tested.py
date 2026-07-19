import unittest
import subprocess

import mutated_hello_world_tested


class TestHelloWorld(unittest.TestCase):
    def test_return(self):
        self.assertEqual('Hello World!', mutated_hello_world_tested.hello_world())
        self.assertEqual(0, subprocess.call(['pylint', 'mutated_hello_world_tested.py']))


if __name__ == '__main__':
    unittest.main()
