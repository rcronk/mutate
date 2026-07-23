""" life.py - a deterministic single-creature performance assay.

Functional information needs a degree of function to measure rarity against: how
well a program plays the game of staying alive and reproducing. This runs one
creature, driven by its own act(), through a single lifetime in a fixed world,
and returns its lifetime reproductive output: how many offspring it manages to
pay for and provision before it dies.

Broken or selfish programs score zero (they crash, starve, or never breed); a
program that feeds itself and breeds when able scores higher. The world and life
parameters are fixed so the assay is a fair, deterministic comparison across
programs. It is single-creature by design: this measures a genome's intrinsic
competence, not population dynamics, which belong to the evolutionary loop.
"""

from creatures import genome, lifecycle

DEFAULT_REGROWTH = 5
DEFAULT_STARTING_FOOD = 20


def reproductive_output(source, *, regrowth=DEFAULT_REGROWTH,
                        starting_food=DEFAULT_STARTING_FOOD):
    """ Runs one creature's life and counts the offspring it produces.

        Each tick the world regrows, the creature decides, eats what it can from
        the pool, breeds if it chose to and is eligible, then ages. A birth costs
        the flat reproduction cost plus whatever fuel the creature endows the
        child with. A program that cannot be run, crashes on an input, or never
        breeds scores zero.
    :param source: The program source
    :param regrowth: Food added to the pool each tick
    :param starting_food: Food in the pool at the start
    :return: Lifetime offspring count, a non-negative integer
    """
    if not genome.is_viable(source):
        return 0
    creature = lifecycle.Lifecycle()
    world = lifecycle.World(food=starting_food, regrowth=regrowth)
    offspring = 0
    while creature.alive and creature.age < creature.max_age:
        world.tick()
        try:
            decision = genome.decide(
                source, age=creature.age, fuel=creature.fuel,
                max_fuel=creature.max_fuel, food_available=world.food, population=1)
        except genome.MisbehavingCreatureError:
            break
        creature.eat(world.request(decision['eat']))
        if decision['reproduce'] and creature.can_reproduce:
            creature.pay_for_reproduction()
            creature.fuel -= min(decision['endowment'], creature.fuel)
            offspring += 1
        creature.tick()
    return offspring
