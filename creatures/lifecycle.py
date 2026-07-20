""" lifecycle.py - the fixed rules a creature cannot mutate away.

Aging, fuel accounting and death live here rather than in the creature's own
source. A creature is Python text and can be mutated, so if it owned its death
check evolution would delete it within a few generations and every creature
would be immortal. Putting the rules in the engine keeps the simulation
meaningful.

Food comes from a single finite pool with per-tick regrowth. Creatures draw
from it in the order they ask, so a creature can starve because others got
there first. That is the competition the 2017 version never had: it counted
fuel down with nothing to eat and no shared resource.
"""

# The 2017 self_mutator used fuel 10, death at age 10, fertile between ages 2
# and 5, and a reproduction cost of 5. Those numbers drive a *mutating*
# population extinct every time, because only about 17% of births produce a
# working creature (see genome.py), so a creature needs roughly six attempts
# just to replace itself and those settings allow about two.
#
# These defaults widen the fertile window and cheapen reproduction enough that
# a mutating population sustains itself. That is the minimum for there to be
# anything to observe: a lineage that cannot reach replacement is not a
# minimal creature, it is a dead one.
DEFAULT_FUEL = 15
DEFAULT_MAX_FUEL = 40
DEFAULT_MAX_AGE = 12
DEFAULT_FERTILE_FROM = 2
DEFAULT_FERTILE_UNTIL = 8
DEFAULT_REPRODUCTION_COST = 1


class DeadCreatureError(Exception):
    """ Raised when something tries to act on a creature that has died. """


class NotFertileError(Exception):
    """ Raised when a creature tries to reproduce while ineligible. """


class Lifecycle:  # pylint: disable=too-many-instance-attributes
    """ The engine-owned state of one creature.

        A plain record of the rules, so the attribute count reflects how many
        independent parameters a life has rather than any design problem.
    """

    # Six independent life parameters, all of which a caller legitimately varies
    # per experiment. Bundling them would add indirection without removing a
    # decision, so the limit is waived rather than worked around.
    def __init__(self, fuel=DEFAULT_FUEL, *,  # pylint: disable=too-many-arguments
                 max_fuel=DEFAULT_MAX_FUEL,
                 max_age=DEFAULT_MAX_AGE, fertile_from=DEFAULT_FERTILE_FROM,
                 fertile_until=DEFAULT_FERTILE_UNTIL,
                 reproduction_cost=DEFAULT_REPRODUCTION_COST):
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.max_age = max_age
        self.fertile_from = fertile_from
        self.fertile_until = fertile_until
        self.reproduction_cost = reproduction_cost
        self.age = 0
        self.alive = True
        self.cause_of_death = None

    def tick(self):
        """ Advances one tick: one older, one fuel poorer, then check for death.

            Fuel is checked before age, so a creature that runs out of both on
            the same tick is recorded as having starved.
        :return: None
        """
        self._require_alive()
        self.age += 1
        self.fuel -= 1
        if self.fuel <= 0:
            self._die('starvation')
        elif self.age >= self.max_age:
            self._die('old_age')

    def eat(self, amount):
        """ Adds fuel, up to the cap.
        :param amount: Food received, which may be less than was asked for
        :return: Fuel actually gained
        """
        self._require_alive()
        before = self.fuel
        self.fuel = min(self.fuel + amount, self.max_fuel)
        return self.fuel - before

    @property
    def can_reproduce(self):
        """ :return: True if inside the fertile window with fuel to spare """
        return (self.alive
                and self.fertile_from <= self.age <= self.fertile_until
                and self.fuel > self.reproduction_cost)

    def pay_for_reproduction(self):
        """ Deducts the cost of producing one offspring.
        :return: None
        """
        if not self.can_reproduce:
            raise NotFertileError(
                f'age {self.age}, fuel {self.fuel}: not eligible to reproduce')
        self.fuel -= self.reproduction_cost

    def _die(self, cause):
        self.alive = False
        self.cause_of_death = cause

    def _require_alive(self):
        if not self.alive:
            raise DeadCreatureError(f'creature died of {self.cause_of_death}')


class World:
    """ The shared food supply every creature draws from. """

    def __init__(self, food, regrowth, max_food=None):
        self.food = food
        self.regrowth = regrowth
        self.max_food = max_food

    def tick(self):
        """ Regrows food, up to the cap if one is set.
        :return: None
        """
        self.food += self.regrowth
        if self.max_food is not None:
            self.food = min(self.food, self.max_food)

    def request(self, amount):
        """ Takes food from the pool, giving whatever is left if the pool is
            short.  Creatures are served in the order they ask, so a creature
            can go hungry because others reached the pool first.
        :param amount: Food wanted
        :return: Food actually given, between 0 and amount
        """
        given = max(0, min(amount, self.food))
        self.food -= given
        return given
