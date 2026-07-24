""" environment.py - a world that provably requires structure, not tuning.

Slice 2 showed the constant food world is solved by any feeding pool, and a
feast/famine world is solved by *tuning one number*, because a cell's energy
already integrates the food signal, so thresholding energy substitutes for
sensing. That does not test whether evolution can build structure.

This world adds a second, independent signal, `safe`, that does not affect
energy and so cannot be proxied by it. Food fluctuates on one period; safety
fluctuates on another. A newborn survives only if it is divided while the world
is safe (a hazard kills the rest) and there is food for it to eat. The best
possible behaviour therefore depends on *two* signals at once, energy (a proxy
for food) and `safe`, so any solution must read a second sensor and combine it.
Verified: a two-signal sensor beats every fixed energy threshold. We specify only
that the optimum needs two inputs, never the code that reads them.
"""

DEFAULT_FEAST = 80
DEFAULT_FOOD_PERIOD = 8
DEFAULT_SAFE_PERIOD = 5


class TwoSignalWorld:
    """ A food supply plus an independent safety signal. """

    def __init__(self, *, feast=DEFAULT_FEAST, food_period=DEFAULT_FOOD_PERIOD,
                 safe_period=DEFAULT_SAFE_PERIOD):
        self.food = 0
        self.safe = True
        self._feast = feast
        self._food_period = food_period
        self._safe_period = safe_period
        self._age = 0

    def tick(self):
        """ Advances food (feast/famine) and safety on their own periods. """
        self._age += 1
        if (self._age // self._food_period) % 2 == 0:
            self.food += self._feast
        self.safe = (self._age // self._safe_period) % 2 == 0

    def request(self, amount):
        """ Serves up to `amount` food, whatever is left if the pool is short. """
        given = max(0, min(int(amount), self.food))
        self.food -= given
        return given


def make_world():
    """ :return: A fresh TwoSignalWorld, as a factory for world.run """
    return TwoSignalWorld()


def newborn_survives(env):
    """ :return: True if a daughter born now survives the hazard (world is safe) """
    return env.safe
