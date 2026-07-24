"""Tests for the cell, the engine-owned state a protein cannot mutate away."""

import unittest

from creatures import lifecycle
from protocell import cell as cell_module
from protocell.ancestors import working_pool
from protocell.cell import Cell


class TestProteinApi(unittest.TestCase):

    def test_eat_turns_food_into_energy(self):
        cell = Cell([], energy=10)
        gained = cell.eat(lifecycle.World(food=100, regrowth=0), 5)
        self.assertEqual(5, gained)
        self.assertEqual(15, cell.energy)

    def test_eat_is_capped_by_the_energy_ceiling(self):
        cell = Cell([], energy=cell_module.MAX_ENERGY - 2)
        self.assertEqual(2, cell.eat(lifecycle.World(food=100, regrowth=0), 50))

    def test_eat_is_limited_by_available_food(self):
        cell = Cell([], energy=10)
        self.assertEqual(3, cell.eat(lifecycle.World(food=3, regrowth=0), 50))


class TestEngineOwnedRules(unittest.TestCase):

    def test_metabolize_costs_energy_and_ages(self):
        cell = Cell([], energy=5)
        cell.metabolize()
        self.assertEqual(5 - cell_module.METABOLIC_COST, cell.energy)
        self.assertEqual(1, cell.age)

    def test_starvation_kills(self):
        cell = Cell([], energy=cell_module.METABOLIC_COST)
        cell.metabolize()
        self.assertFalse(cell.alive)

    def test_no_division_without_a_request(self):
        self.assertIsNone(Cell([], energy=50).spawn_daughter())

    def test_division_produces_a_daughter_when_rich(self):
        cell = Cell(working_pool(), energy=50)
        cell.divide()
        daughter = cell.spawn_daughter()
        self.assertIsNotNone(daughter)
        self.assertGreater(daughter.energy, 0)
        self.assertLess(cell.energy, 50)  # the parent paid for it

    def test_division_denied_when_too_poor(self):
        cell = Cell(working_pool(), energy=cell_module.DIVISION_THRESHOLD)
        cell.divide()
        self.assertIsNone(cell.spawn_daughter())

    def test_dump_is_readable_source(self):
        self.assertIn('def protein', Cell(working_pool()).dump())


if __name__ == '__main__':
    unittest.main()
