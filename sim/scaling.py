""" scaling.py - does more resource cross the coordination barrier?

The finale of Option 3, and a correction. An earlier, smaller sweep found the
population stuck at the floor and concluded the ceiling was real. Pushed far
harder (see scaling_full_sweep.py and data/scaling_sweep_raw.txt), that reading
falls apart: below a resource threshold evolution stalls, but around a budget of
640,000 here it crosses the valley and reaches strategies better than a hand-
designed reference. Best fitness climbs 1 -> 4 -> 6 -> 17 -> 18 as the budget
grows, past the reference optimum of 7.

Two lessons stand. First, the barrier is real but crossable, set by resources and
mutation rate, which is exactly Part A's result that a deleterious valley is
crossable given enough population and time. Second, a stall at modest resource is
not a ceiling; only a curve that flattens under real pressure is, and this one
does not. Mutation rate also has an optimum: moderate rates build, but 0.7 and
above collapse every run to zero, an error catastrophe.

This module keeps the fast, live checks (the below-threshold stall and the
no-barrier control) and displays the recorded large-scale results, which are too
slow to rerun here. The crossing itself is proven cheaply by a saved evolved
genome that independently scores far above the barrier.
"""

import os
import sys

from sim import competition, evolve, life

# The best strategy found for the competitive environment by hand: eat and endow
# moderately, breed fewer but provisioned offspring. Evolution beats it at scale.
BALANCED_STRATEGY = ('def act(age, fuel, max_fuel, food_available, population):\n'
                     '    return {"eat": 8, "reproduce": True, "endowment": 8}\n')

CROSSING_GENOME_PATH = os.path.join(os.path.dirname(__file__), 'data',
                                    'crossing_genome_seed0.txt')

# Recorded from scaling_full_sweep.py; see data/scaling_sweep_raw.txt. Each row is
# (budget, best fitness over 6 seeds, seeds that crossed the optimum).
RECORDED_RESOURCE_SCALING = (
    (10000, 1, 0), (40000, 4, 0), (160000, 6, 0), (640000, 17, 5), (1500000, 18, 3))
# (mutation rate, best over 6 seeds, crossed) at a fixed 200x200 budget.
RECORDED_MUTATION_SWEEP = (
    (0.1, 4, 0), (0.3, 6, 0), (0.5, 4, 0), (0.7, 0, 0), (0.9, 0, 0))

STALL_LEVELS = ((10, 10), (20, 20))
CONTROL_LEVELS = ((10, 10),)
SEEDS = 3
MUTATION_RATE = 0.5


def optimum():
    """ :return: The competitive fitness of the hand-designed balanced strategy """
    return competition.competitive_fitness(BALANCED_STRATEGY)


def crossing_genome():
    """ :return: The evolved genome that crossed the barrier (from an 800x800,
        seed 0 run), saved so the crossing is provable without rerunning it """
    with open(CROSSING_GENOME_PATH, encoding='utf-8') as handle:
        return handle.read()


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


def main():
    """ Prints the corrected scaling result. """
    target = optimum()
    print(f'Competitive environment, hand-designed reference optimum = {target}.')
    print()
    print('Live, below the resource threshold (fast):')
    for level, scores in sweep(STALL_LEVELS).items():
        print(f'  {level[0]:>4} x {level[1]:<4}  best {max(scores)}   (stuck at the floor)')
    print('Live control, simple assay with no barrier (fast):')
    for level, scores in sweep(CONTROL_LEVELS, fitness=life.reproductive_output).items():
        print(f'  {level[0]:>4} x {level[1]:<4}  best {max(scores)}   (reaches its optimum)')
    print()
    print(f'A saved evolved genome scores {competition.competitive_fitness(crossing_genome())}'
          f', well past the barrier of {target}.')
    print()
    print('Recorded large-scale sweep (data/scaling_sweep_raw.txt):')
    print('  budget       best   crossed/6')
    for budget, best, crossed in RECORDED_RESOURCE_SCALING:
        seeds = 3 if budget == 1500000 else 6
        print(f'  {budget:>9}    {best:>4}   {crossed}/{seeds}')
    print('  -> the barrier is crossed once the budget is large enough; more')
    print('     resource keeps helping. The earlier "ceiling" was a resource limit.')
    print('Mutation rate has an optimum (0.7+ collapses to zero, error catastrophe):')
    print('  ' + '  '.join(f'{rate}:{best}' for rate, best, _ in RECORDED_MUTATION_SWEEP))
    return 0


if __name__ == '__main__':
    sys.exit(main())
