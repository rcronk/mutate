""" buildability.py - how the cost of building a K-part structure depends on K.

Slice 6. With the engine validated (waiting time and fixation both match the
math, see analytic.py), we can now ask the question the whole apparatus is for:
how hard is it to build a structure that needs K coordinated parts, and how much
of the answer is carried by the assumption that a gradient of useful
intermediates exists?

Two regimes, same engine, same mutation supply:

  - NO GRADIENT: every intermediate is neutral. Nothing rewards a half-built
    structure, so selection is blind to progress; only mutation and drift cross
    the gap. This is the honest hard case, and the one that applies when a part
    is useless until the whole assembly is present.
  - GRADIENT: each completed step is itself beneficial (selection coefficient
    `selection`), so a partial structure is favored and selection carries it up
    step by step. This is the assumption most digital-evolution successes rely on.

The readout is buildability(K): the mean generations to first build the full
structure, and the fraction of runs that build it within a fixed resource budget.
The contrast between the two regimes is the point: it measures, in generations,
what the gradient assumption is worth.

No intermediate reward is ever hand-authored in the no-gradient regime; that is
the bias guard. When we study the gradient, it is an explicit, reported variable.
"""

import random
import statistics
import sys

from kaxis import population

POP_SIZE = 1000
STEP_RATE = 5e-4
SELECTION = 0.1
BUDGET = 300000
REPLICATES = 60
COORDINATION_NUMBERS = (1, 2, 3, 4, 5, 6)


def _neutral_fitness(coordination):
    """ :return: All-neutral fitness for a K-step genome (no gradient). """
    return [1.0] * (coordination + 1)


def _gradient_fitness(coordination, selection):
    """ :return: Fitness rising by (1+selection) per completed step (a gradient). """
    return [(1.0 + selection) ** step for step in range(coordination + 1)]


def build_stats(coordination, *, gradient, pop_size=POP_SIZE, rate=STEP_RATE,
                selection=SELECTION, budget=BUDGET, replicates=REPLICATES, seed=0):
    # The knobs are all reported experiment parameters, so they are explicit
    # arguments rather than hidden state.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """ :return: (fraction built within budget, mean generations among those built). """
    rates = (rate,) * coordination
    fitness = (_gradient_fitness(coordination, selection) if gradient
               else _neutral_fitness(coordination))
    rng = random.Random(seed)
    times = [population.waiting_time(pop_size, rates, rng, fitness=fitness,
                                     max_generations=budget)
             for _ in range(replicates)]
    built = [time for time in times if time < budget]
    fraction = len(built) / replicates
    mean_time = statistics.mean(built) if built else float('inf')
    return fraction, mean_time


def curve(*, gradient, coordination_numbers=COORDINATION_NUMBERS, **knobs):
    """ :return: {K: (fraction built, mean time)} across the coordination numbers. """
    return {coordination: build_stats(coordination, gradient=gradient,
                                      seed=100 + coordination, **knobs)
            for coordination in coordination_numbers}


def main():
    """ Prints buildability(K) for the no-gradient and gradient regimes. """
    no_gradient = curve(gradient=False)
    gradient = curve(gradient=True)
    print(f'Buildability(K): pop={POP_SIZE}, step rate={STEP_RATE}, '
          f'selection={SELECTION}, {REPLICATES} runs each.')
    print('Mean generations to build a K-part structure:')
    print(f"  {'K':>2}  {'no gradient':>12}  {'gradient':>10}  "
          f"{'cost ratio':>10}")
    for coordination in COORDINATION_NUMBERS:
        neutral_time = no_gradient[coordination][1]
        gradient_time = gradient[coordination][1]
        ratio = neutral_time / gradient_time if gradient_time else float('inf')
        print(f"  {coordination:>2}  {neutral_time:>12.1f}  {gradient_time:>10.1f}  "
              f"{ratio:>9.1f}x")
    print()
    print('With a gradient the cost grows about linearly with K. Without one it')
    print('grows far faster, so the cost ratio widens with every added part: the')
    print('gradient assumption is doing the work. Where real biology sits on this')
    print('axis (how often a partial structure is actually rewarded) is the')
    print('empirical question this makes measurable, not one we settle here.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
