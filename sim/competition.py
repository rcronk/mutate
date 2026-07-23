""" competition.py - an environment where complexity pays.

The solo assay (sim.life) rewards a trivial strategy: eat all you can, breed
every tick, and give offspring nothing, because offspring are never simulated so
investment is pure cost. Under it, cumulative selection strips the ancestor's one
non-trivial feature (endowment). That is the wrong environment for asking whether
evolution can build.

Here the offspring are simulated, and they compete. A creature's offspring are
dropped into one finite, scarce food pool and must survive it; fitness is how
many of them live long enough to reproduce. Now the r/K tradeoff is real: many
offspring endowed with nothing starve in the scramble, while a few well-provided
ones survive. Provisioning and restraint, which the solo assay punished, pay.
Nothing about a specific complex behaviour is rewarded, only surviving
competition, so the environment does not smuggle in what counts as complex.
"""

from creatures import genome, lifecycle
from sim import life

DEFAULT_REGROWTH = 2
DEFAULT_STARTING_FOOD = 8


def competitive_fitness(source, *, regrowth=DEFAULT_REGROWTH,
                        starting_food=DEFAULT_STARTING_FOOD):
    """ Fitness as the number of a program's offspring that survive competition.

        The parent lives a normal solo life to produce its offspring, each
        carrying the endowment the parent chose. Those offspring are then placed
        together in one scarce, finite food pool, drawing food in turn, and run
        until they all die or reach the end of life. Fitness is how many of them
        reproduce at least once.
    :param source: The program source
    :param regrowth: Food added to the shared pool each tick
    :param starting_food: Food in the shared pool at the start
    :return: Count of offspring that reproduce, a non-negative integer
    """
    endowments = life.offspring_endowments(source)
    if not endowments:
        return 0
    world = lifecycle.World(food=starting_food, regrowth=regrowth)
    cohort = [lifecycle.Lifecycle(fuel=endowment) for endowment in endowments]
    reproduced = [False] * len(cohort)
    for _ in range(lifecycle.DEFAULT_MAX_AGE):
        world.tick()
        alive = sum(1 for creature in cohort if creature.alive)
        if alive == 0:
            break
        for index, creature in enumerate(cohort):
            if creature.alive and _live_one_tick(source, creature, world, alive):
                reproduced[index] = True
    return sum(reproduced)


def _live_one_tick(source, creature, world, population):
    """ Advances one competing creature by a single tick.
    :return: True if the creature reproduced this tick
    """
    try:
        decision = genome.decide(
            source, age=creature.age, fuel=creature.fuel, max_fuel=creature.max_fuel,
            food_available=world.food, population=population)
    except genome.MisbehavingCreatureError:
        creature.tick()  # a creature that cannot act just ages toward starvation
        return False
    creature.eat(world.request(decision['eat']))
    reproduced = False
    if decision['reproduce'] and creature.can_reproduce:
        creature.pay_for_reproduction()
        creature.fuel -= min(decision['endowment'], creature.fuel)
        reproduced = True
    creature.tick()
    return reproduced
