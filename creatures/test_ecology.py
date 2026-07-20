"""Tests that a mutating population can actually sustain itself.

These are slower than the unit tests because they run whole populations, but
they pin the claim the whole phase depends on: food alone limits the
population, and no artificial concurrency cap is needed as an ecological
mechanism.

Getting here required two fixes. The ancestor used to hardcode `2 <= age <= 5`,
which capped every creature at about two breeding attempts regardless of the
engine's fertile window. And the 2017 lifecycle numbers allowed roughly two
attempts when about six are needed, since only ~17% of births produce a working
creature. Together those drove every population extinct.
"""

import unittest

from creatures import genome, lifecycle


def run_population(*, regrowth, ticks=120, founders=20, cap=None, mutate=True):
    """Runs a population in-process and reports what happened.

    :param regrowth: Food added to the shared pool each tick
    :param ticks: How long to run
    :param founders: Starting population
    :param cap: Optional hard ceiling, used only to prove it is not needed
    :param mutate: Whether offspring are mutated
    :return: dict of outcomes
    """
    world = lifecycle.World(food=regrowth * 5, regrowth=regrowth)
    pop = [[lifecycle.Lifecycle(),
            genome.Genome(genome.ANCESTOR_SOURCE, seed=i, identity=str(i), generation=1),
            0]
           for i in range(founders)]
    history = []
    deaths = {'starvation': 0, 'old_age': 0, 'crashed': 0}
    max_generation = 1

    for _ in range(ticks):
        world.tick()
        newborns = []
        for entry in pop:
            life, gene, births = entry
            if not life.alive:
                continue
            try:
                decision = genome.decide(gene.source, age=life.age, fuel=life.fuel,
                                         max_fuel=life.max_fuel)
            except genome.MisbehavingCreatureError:
                life.alive = False
                deaths['crashed'] += 1
                continue
            life.eat(world.request(decision['eat']))
            room = cap is None or len(pop) + len(newborns) < cap
            if decision['reproduce'] and life.can_reproduce and room:
                child = gene.child(birth_index=births) if mutate else gene
                entry[2] += 1
                life.pay_for_reproduction()
                if child is not None:
                    newborns.append([lifecycle.Lifecycle(), child, 0])
                    max_generation = max(max_generation, child.generation)
            life.tick()
            if not life.alive and life.cause_of_death in deaths:
                deaths[life.cause_of_death] += 1
        pop = [e for e in pop if e[0].alive] + newborns
        history.append(len(pop))
        if not pop:
            break

    return {'history': history, 'final': len(pop), 'peak': max(history),
            'deaths': deaths, 'max_generation': max_generation,
            'extinct': not pop}


class TestPopulationSurvives(unittest.TestCase):
    """Without this, there is nothing to observe in phase 3."""

    def test_a_mutating_population_does_not_go_extinct(self):
        result = run_population(regrowth=400)
        self.assertFalse(result['extinct'],
                         'the ancestor cannot reach replacement rate')
        self.assertGreater(result['final'], 0)

    def test_lineages_reach_later_generations(self):
        """Evolution has to actually be happening, not just survival of the
        founders."""
        result = run_population(regrowth=400)
        self.assertGreater(result['max_generation'], 5)

    def test_mutation_costs_lives(self):
        """Creatures that parse but crash die in the world, and that shows up
        as a real cause of death rather than being hidden at birth."""
        result = run_population(regrowth=400)
        self.assertGreater(result['deaths']['crashed'], 0)

    def test_a_non_mutating_population_never_crashes(self):
        """Control: every crash in the mutating run is caused by mutation."""
        result = run_population(regrowth=400, mutate=False)
        self.assertEqual(0, result['deaths']['crashed'])


class TestFoodIsTheLimiter(unittest.TestCase):
    """The point: scarcity limits the population, so no artificial cap is
    needed as an ecological mechanism. A process cap is a safety valve for the
    machine, not a rule of the world."""

    def test_more_food_supports_more_creatures(self):
        lean = run_population(regrowth=60)
        rich = run_population(regrowth=400)
        self.assertGreater(rich['peak'], lean['peak'])

    def test_scarcity_limits_by_suppressing_births_not_by_starving_adults(self):
        """Measured, and not what I expected. Creatures carry a fuel reserve, so
        they ride out shortages rather than dying of them: starvation is almost
        never the proximate cause of death.

        What scarcity actually does is hold fuel below the reproduction
        threshold, so hungry creatures are refused reproduction and the birth
        rate falls. Food throttles fertility, not survival.
        """
        lean = run_population(regrowth=15, ticks=80)
        rich = run_population(regrowth=400, ticks=80)
        self.assertLess(lean['peak'], rich['peak'])
        self.assertGreater(rich['deaths']['old_age'], lean['deaths']['old_age'])

    def test_too_little_food_ends_in_extinction(self):
        """The limit has teeth: below replacement, the population dies out."""
        self.assertTrue(run_population(regrowth=15, ticks=80)['extinct'])

    def test_population_stays_bounded_without_any_cap(self):
        """No cap is passed at all here. If food did not limit growth this
        would grow without bound until the machine gave out."""
        result = run_population(regrowth=400, cap=None)
        self.assertLess(result['peak'], 5000)

    def test_starving_creatures_cannot_breed(self):
        """Which is the mechanism that makes food a limiter: a creature short
        of fuel is refused reproduction by the engine, so scarcity throttles
        births directly."""
        creature = lifecycle.Lifecycle(fuel=2, reproduction_cost=5)
        creature.tick()
        self.assertFalse(creature.can_reproduce)


if __name__ == '__main__':
    unittest.main()
