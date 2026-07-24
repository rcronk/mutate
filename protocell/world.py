""" world.py - a population of cells competing for finite food.

Runs many cells against one regrowing food pool. Each tick every living cell
executes its proteins in random order, pays its metabolic cost, and may divide;
daughters join the population. Cells that starve or age out are removed. Nothing
is selected by hand: cells that feed and divide leave more descendants, cells
that do not die out. That is the whole of the selection.
"""

import dataclasses
import random

from creatures import lifecycle
from protocell.cell import Cell

DEFAULT_FOOD = 200
DEFAULT_REGROWTH = 60


@dataclasses.dataclass
class Result:
    """ What one run produced. """
    history: list          # population size at each tick, including the start
    survivors: list        # the living cells at the end
    generations: int       # how many divisions happened in total

    @property
    def extinct(self):
        """ :return: True if the population died out """
        return not self.survivors


def _step(population, env, rng, mutate, newborn_survives):
    """ Runs one tick: everyone acts, metabolizes, and maybe divides.

        A daughter is discarded if `newborn_survives` rejects the current
        environment (a hazard), but the parent has already paid for her, so
        dividing at the wrong moment is a pure loss.
    :return: (the next population, number of surviving daughters)
    """
    env.tick()
    rng.shuffle(population)
    daughters = []
    for cell in population:
        if not cell.alive:
            continue
        order = list(cell.proteins)
        rng.shuffle(order)
        for protein in order:
            protein.execute(cell, env)
        cell.metabolize()
        daughter = cell.spawn_daughter(mutate=mutate)
        if daughter is not None and (newborn_survives is None or newborn_survives(env)):
            daughters.append(daughter)
    return [cell for cell in population if cell.alive] + daughters, len(daughters)


# Eight knobs, all keyword-only run parameters; bundling them would only hide
# what a run is.
def run(founder_pool, *, founders=10, ticks=200,  # pylint: disable=too-many-arguments
        food=DEFAULT_FOOD, regrowth=DEFAULT_REGROWTH, seed=0, mutate=None,
        make_env=None, newborn_survives=None):
    """ Runs a population from a founder protein pool.
    :param founder_pool: A list of Proteins every founder starts with
    :param founders: How many founder cells
    :param ticks: How many ticks to run
    :param food: Starting food in the default constant world
    :param regrowth: Food added each tick in the default constant world
    :param seed: Random seed; the same seed reproduces the run
    :param mutate: Optional callable applied to a daughter's protein list
    :param make_env: Optional factory for a fresh environment; the default is a
        constant regrowing food pool
    :param newborn_survives: Optional predicate on the environment; a daughter
        born when it is false dies (a hazard)
    :return: A Result
    """
    rng = random.Random(seed)
    env = make_env() if make_env is not None else lifecycle.World(food=food, regrowth=regrowth)
    population = [Cell(list(founder_pool)) for _ in range(founders)]
    history = [len(population)]
    divisions = 0
    for _ in range(ticks):
        population, born = _step(population, env, rng, mutate, newborn_survives)
        divisions += born
        history.append(len(population))
        if not population:
            break
    return Result(history=history, survivors=population, generations=divisions)
