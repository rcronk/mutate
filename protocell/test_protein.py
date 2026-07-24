"""Tests for a single protein."""

import unittest

from protocell.cell import Cell
from protocell.protein import Protein

WRITES_REGISTER = 'def protein(cell, env):\n    cell.registers[0] = 1\n'


class TestFolding(unittest.TestCase):

    def test_valid_source_folds(self):
        self.assertTrue(Protein(WRITES_REGISTER).folded)

    def test_a_syntax_error_misfolds(self):
        self.assertFalse(Protein('def protein(').folded)

    def test_source_without_protein_misfolds(self):
        self.assertFalse(Protein('x = 1').folded)


class TestExecution(unittest.TestCase):

    def test_a_folded_protein_applies_its_effect(self):
        cell = Cell([])
        Protein(WRITES_REGISTER).execute(cell, None)
        self.assertEqual(1, cell.registers[0])

    def test_a_misfolded_protein_does_nothing(self):
        cell = Cell([])
        Protein('def protein(').execute(cell, None)  # must not raise
        self.assertEqual(0, cell.registers[0])

    def test_a_runtime_error_is_swallowed(self):
        crashes = 'def protein(cell, env):\n    raise ValueError("boom")\n'
        Protein(crashes).execute(Cell([]), None)  # must not raise


if __name__ == '__main__':
    unittest.main()
