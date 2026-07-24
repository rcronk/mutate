""" life.py - deterministic single-creature life simulation.

Functional information needs a degree of function to measure rarity against: how
well a program plays the game of staying alive and reproducing. This runs one
creature, driven by its own act(), through a single lifetime in a fixed world.

`offspring_endowments` is the shared core: it returns the endowment each birth
carried, so callers can either count births (reproductive_output, the solo
assay) or hand those offspring to a competitive world (sim.competition). Broken
or selfish programs produce no surviving line; a program that feeds itself and
breeds when able produces more.
"""

from creatures import genome, lifecycle

DEFAULT_REGROWTH = 5
DEFAULT_STARTING_FOOD = 20


def offspring_endowments(source, *, starting_fuel=lifecycle.DEFAULT_FUEL,
                         regrowth=DEFAULT_REGROWTH, starting_food=DEFAULT_STARTING_FOOD):
    """ Runs one creature's life and returns the endowment of each birth.

        Each tick the world regrows, the creature decides, eats what it can from
        the pool, breeds if it chose to and is eligible (paying the flat cost and
        transferring an endowment to the child), then ages. A program that cannot
        be run or crashes on an input ends its life there.
    :param source: The program source
    :param starting_fuel: Fuel the creature begins with (an offspring begins with
        only the fuel its parent endowed it)
    :param regrowth: Food added to the pool each tick
    :param starting_food: Food in the pool at the start
    :return: A list with one endowment value per birth, empty if none
    """
    if not genome.is_viable(source):
        return []
    creature = lifecycle.Lifecycle(fuel=starting_fuel)
    world = lifecycle.World(food=starting_food, regrowth=regrowth)
    endowments = []
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
            endowment = min(decision['endowment'], creature.fuel)
            creature.fuel -= endowment
            endowments.append(endowment)
        creature.tick()
    return endowments


def reproductive_output(source, *, regrowth=DEFAULT_REGROWTH,
                        starting_food=DEFAULT_STARTING_FOOD):
    """ The solo assay: how many offspring a program produces in its lifetime.
    :return: Lifetime offspring count, a non-negative integer
    """
    return len(offspring_endowments(source, regrowth=regrowth,
                                    starting_food=starting_food))
