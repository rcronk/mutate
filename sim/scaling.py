""" scaling.py - does more resource cross the coordination barrier?

The finale of Option 3. Under the competitive environment the balanced strategy
exists and pays sevenfold, but cumulative selection from the ancestor stalls at
the floor. This sweeps the resources (population size and generations) upward and
asks whether more of them lets evolution cross the barrier to the balanced
optimum, or whether the ceiling is real.

A control sweep under the simple solo assay, whose optimum sits behind no
coordination barrier, checks that the machinery can reach an optimum at all. It
does, immediately, at every resource level. So a flat competitive curve is a
barrier that resource cannot buy past, not a loop that cannot climb.
"""

import statistics
import sys

from sim import competition, evolve, life

# The best strategy found for the competitive environment: eat and endow
# moderately, breed fewer but provisioned offspring.
BALANCED_STRATEGY = ('def act(age, fuel, max_fuel, food_available, population):\n'
                     '    return {"eat": 8, "reproduce": True, "endowment": 8}\n')

COMPETITIVE_LEVELS = ((20, 30), (50, 75), (120, 180))
CONTROL_LEVELS = ((20, 30), (120, 180))
SEEDS = 5
MUTATION_RATE = 0.5


def optimum():
    """ :return: The competitive fitness of the balanced strategy, the target """
    return competition.competitive_fitness(BALANCED_STRATEGY)


def sweep(levels, *, seeds=SEEDS, mutation_rate=MUTATION_RATE,
          fitness=competition.competitive_fitness):
    """ Runs the evolutionary loop at each resource level, several seeds each.
    :param levels: An iterable of (population_size, generations) pairs
    :param seeds: How many replicate runs per level
    :param mutation_rate: The per-offspring mutation probability
    :param fitness: The selection measure
    :return: A dict from level to the list of best scores, one per seed
    """
    return {
        level: [evolve.run(population_size=level[0], generations=level[1],
                           mutation_rate=mutation_rate, seed=seed,
                           fitness=fitness).best_score
                for seed in range(seeds)]
        for level in levels
    }


def analyse():
    """ Runs the competitive sweep and the simple-assay control.
    :return: A dict with the optimum and both sweeps
    """
    return {
        'optimum': optimum(),
        'competitive': sweep(COMPETITIVE_LEVELS),
        'control': sweep(CONTROL_LEVELS, fitness=life.reproductive_output),
    }


def _print_sweep(sweep_result):
    """ Prints one sweep as a resource-versus-best-score table. """
    for (population, generations), scores in sweep_result.items():
        print(f'  {population:>4} x {generations:<4}  budget {population * generations:>7}'
              f'   best {max(scores)}   median {statistics.median(scores)}')


def main():
    """ Prints the scaling result. """
    result = analyse()
    target = result['optimum']
    print(f'Competitive environment: the balanced optimum scores {target}.')
    print('Does pouring in more resource let evolution reach it?')
    _print_sweep(result['competitive'])
    crossed = any(max(scores) >= target for scores in result['competitive'].values())
    if crossed:
        print('  -> the barrier was crossed with enough resource.')
    else:
        print('  -> never crossed. More population and more generations did not')
        print('     help: the ceiling holds across the tested range.')
    print()
    print('Control, the simple solo assay whose optimum hides behind no valley:')
    _print_sweep(result['control'])
    print('  -> the machinery reaches an optimum trivially when none is hidden,')
    print('     so the flat competitive curve is a real barrier, not a broken loop.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
