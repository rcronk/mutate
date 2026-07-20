"""Tests for the lifecycle engine and the shared food pool.

Written before the implementation.

Two design decisions are pinned here. The engine owns aging, fuel and death, so
a creature cannot mutate away its own death check. And food comes from a single
finite pool with per-tick regrowth, so creatures genuinely compete and a
population limits itself instead of growing without bound.

The 2017 version had neither: fuel counted down with nothing to eat, and there
was no competition at all.
"""

import unittest

from creatures import lifecycle


class TestLifecycleBasics(unittest.TestCase):

    def test_starts_alive_with_full_fuel(self):
        creature = lifecycle.Lifecycle(fuel=10)
        self.assertTrue(creature.alive)
        self.assertEqual(0, creature.age)
        self.assertEqual(10, creature.fuel)
        self.assertIsNone(creature.cause_of_death)

    def test_a_tick_costs_one_age_and_one_fuel(self):
        creature = lifecycle.Lifecycle(fuel=10)
        creature.tick()
        self.assertEqual(1, creature.age)
        self.assertEqual(9, creature.fuel)

    def test_eating_adds_fuel(self):
        creature = lifecycle.Lifecycle(fuel=5)
        creature.eat(3)
        self.assertEqual(8, creature.fuel)

    def test_fuel_is_capped(self):
        """Otherwise a creature could hoard without limit."""
        creature = lifecycle.Lifecycle(fuel=5, max_fuel=10)
        creature.eat(100)
        self.assertEqual(10, creature.fuel)


class TestDeath(unittest.TestCase):

    def test_dies_of_starvation_when_fuel_runs_out(self):
        creature = lifecycle.Lifecycle(fuel=2)
        creature.tick()
        creature.tick()
        self.assertFalse(creature.alive)
        self.assertEqual('starvation', creature.cause_of_death)

    def test_dies_of_old_age_at_the_limit(self):
        creature = lifecycle.Lifecycle(fuel=1000, max_age=3)
        for _ in range(3):
            creature.tick()
        self.assertFalse(creature.alive)
        self.assertEqual('old_age', creature.cause_of_death)

    def test_starvation_takes_precedence_when_both_would_apply(self):
        """A creature that runs out of fuel on the same tick it ages out is
        recorded as starved, since fuel is checked first."""
        creature = lifecycle.Lifecycle(fuel=1, max_age=1)
        creature.tick()
        self.assertEqual('starvation', creature.cause_of_death)

    def test_ticking_a_dead_creature_is_rejected(self):
        creature = lifecycle.Lifecycle(fuel=1)
        creature.tick()
        with self.assertRaises(lifecycle.DeadCreatureError):
            creature.tick()

    def test_a_dead_creature_cannot_eat(self):
        creature = lifecycle.Lifecycle(fuel=1)
        creature.tick()
        with self.assertRaises(lifecycle.DeadCreatureError):
            creature.eat(5)


class TestReproduction(unittest.TestCase):

    def test_too_young_to_reproduce(self):
        creature = lifecycle.Lifecycle(fuel=100)
        self.assertFalse(creature.can_reproduce)

    def test_reproduces_within_the_fertile_window(self):
        creature = lifecycle.Lifecycle(fuel=100, fertile_from=2, fertile_until=5)
        creature.tick()
        creature.tick()
        self.assertTrue(creature.can_reproduce)

    def test_too_old_to_reproduce(self):
        creature = lifecycle.Lifecycle(fuel=100, fertile_from=2, fertile_until=3)
        for _ in range(4):
            creature.tick()
        self.assertFalse(creature.can_reproduce)

    def test_cannot_reproduce_without_enough_fuel(self):
        """Reproduction costs fuel, so a starving creature cannot breed."""
        creature = lifecycle.Lifecycle(fuel=100, fertile_from=1, reproduction_cost=20)
        creature.tick()
        self.assertTrue(creature.can_reproduce)
        creature.fuel = 5
        self.assertFalse(creature.can_reproduce)

    def test_reproducing_costs_fuel(self):
        creature = lifecycle.Lifecycle(fuel=100, fertile_from=1, reproduction_cost=20)
        creature.tick()
        creature.pay_for_reproduction()
        self.assertEqual(79, creature.fuel)

    def test_cannot_pay_when_ineligible(self):
        creature = lifecycle.Lifecycle(fuel=100)
        with self.assertRaises(lifecycle.NotFertileError):
            creature.pay_for_reproduction()


class TestWorldFoodPool(unittest.TestCase):

    def test_starts_with_the_given_food(self):
        world = lifecycle.World(food=50, regrowth=10)
        self.assertEqual(50, world.food)

    def test_regrows_each_tick(self):
        world = lifecycle.World(food=0, regrowth=10)
        world.tick()
        self.assertEqual(10, world.food)

    def test_regrowth_is_capped(self):
        world = lifecycle.World(food=95, regrowth=10, max_food=100)
        world.tick()
        self.assertEqual(100, world.food)

    def test_requesting_food_removes_it_from_the_pool(self):
        world = lifecycle.World(food=50, regrowth=0)
        self.assertEqual(3, world.request(3))
        self.assertEqual(47, world.food)

    def test_an_empty_pool_gives_nothing(self):
        world = lifecycle.World(food=0, regrowth=0)
        self.assertEqual(0, world.request(5))

    def test_a_partial_pool_gives_what_is_left(self):
        """This is the competition: the last creature to ask goes hungry."""
        world = lifecycle.World(food=2, regrowth=0)
        self.assertEqual(2, world.request(5))
        self.assertEqual(0, world.food)
        self.assertEqual(0, world.request(5))

    def test_food_is_never_negative(self):
        world = lifecycle.World(food=1, regrowth=0)
        world.request(100)
        self.assertGreaterEqual(world.food, 0)


class TestCompetition(unittest.TestCase):
    """The behaviour the 2017 version could not produce."""

    def test_creatures_that_ask_first_are_fed_first(self):
        world = lifecycle.World(food=3, regrowth=0)
        early = lifecycle.Lifecycle(fuel=5)
        late = lifecycle.Lifecycle(fuel=5)
        early.eat(world.request(3))
        late.eat(world.request(3))
        self.assertEqual(8, early.fuel)
        self.assertEqual(5, late.fuel)

    def test_scarcity_starves_the_population_down(self):
        """max_age is raised so old age cannot confound the result: everything
        that dies here died of starvation."""
        world = lifecycle.World(food=0, regrowth=2)
        population = [lifecycle.Lifecycle(fuel=3, max_age=100) for _ in range(10)]
        for _ in range(20):
            world.tick()
            for creature in population:
                if creature.alive:
                    creature.eat(world.request(1))
                    creature.tick()
        survivors = [c for c in population if c.alive]
        self.assertGreater(len(survivors), 0, 'total extinction means the world is too harsh')
        self.assertLess(len(survivors), 10, 'nobody starved, so there was no competition')

    def test_everyone_who_died_under_scarcity_starved(self):
        """Not old age. This is the point of the food pool."""
        world = lifecycle.World(food=0, regrowth=2)
        population = [lifecycle.Lifecycle(fuel=3, max_age=100) for _ in range(10)]
        for _ in range(20):
            world.tick()
            for creature in population:
                if creature.alive:
                    creature.eat(world.request(1))
                    creature.tick()
        causes = {c.cause_of_death for c in population if not c.alive}
        self.assertEqual({'starvation'}, causes)

    def test_carrying_capacity_tracks_the_regrowth_rate(self):
        """The population settles at roughly however many creatures the world
        can feed, which is what makes it self-limiting without a 2D map."""
        for regrowth in (2, 4, 6):
            with self.subTest(regrowth=regrowth):
                world = lifecycle.World(food=0, regrowth=regrowth)
                population = [lifecycle.Lifecycle(fuel=3, max_age=100)
                              for _ in range(20)]
                for _ in range(30):
                    world.tick()
                    for creature in population:
                        if creature.alive:
                            creature.eat(world.request(1))
                            creature.tick()
                survivors = sum(c.alive for c in population)
                self.assertEqual(regrowth, survivors)

    def test_abundance_keeps_everyone_alive(self):
        world = lifecycle.World(food=1000, regrowth=1000)
        population = [lifecycle.Lifecycle(fuel=3, max_age=100) for _ in range(10)]
        for _ in range(20):
            world.tick()
            for creature in population:
                creature.eat(world.request(1))
                creature.tick()
        self.assertEqual(10, len([c for c in population if c.alive]))


if __name__ == '__main__':
    unittest.main()
