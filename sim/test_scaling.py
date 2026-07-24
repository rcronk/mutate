"""Tests for the resource scaling sweep.

Small, fast resource levels here; the committed experiment runs larger ones. The
claim under test is the finale of Option 3: under competition, more resource does
not carry evolution across the coordination barrier, while the same machinery
reaches its optimum at once when no barrier is in the way.
"""

import unittest

from sim import life, scaling


class TestScaling(unittest.TestCase):

    def test_the_balanced_optimum_is_pinned(self):
        self.assertEqual(7, scaling.optimum())

    def test_competition_stays_below_the_optimum_as_resources_grow(self):
        result = scaling.sweep([(10, 10), (20, 20)], seeds=2)
        self.assertEqual({(10, 10): [1, 1], (20, 20): [1, 1]}, result)
        for scores in result.values():
            self.assertTrue(all(score < scaling.optimum() for score in scores),
                            'competition should not cross the barrier')

    def test_the_control_reaches_its_optimum_immediately(self):
        # No barrier: the same loop climbs past the competitive optimum at once.
        result = scaling.sweep([(10, 10)], seeds=2, fitness=life.reproductive_output)
        self.assertTrue(all(score > scaling.optimum() for score in result[(10, 10)]))

    def test_sweep_is_deterministic(self):
        self.assertEqual(scaling.sweep([(15, 15)], seeds=2),
                         scaling.sweep([(15, 15)], seeds=2))


if __name__ == '__main__':
    unittest.main()
