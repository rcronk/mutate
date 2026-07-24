""" scaling_full_sweep.py - the full adversarial scaling sweep.

Regenerates the recorded results in data/scaling_sweep_raw.txt. This is the run
that overturned the earlier "ceiling holds" reading: it pushes resources far
past the committed sweep and sweeps mutation rate, actively trying to cross the
coordination barrier. It is slow (roughly an hour), which is why the numbers are
recorded and the fast experiment lives in scaling.py.

Run: python -m sim.scaling_full_sweep
"""

import sys
import time

from sim import competition, evolve, scaling

RESOURCE_LEVELS = ((100, 100), (200, 200), (400, 400), (800, 800))
MUTATION_RATES = (0.1, 0.3, 0.5, 0.7, 0.9)
MUTATION_LEVEL = (200, 200)
STRESS_LEVEL = (1500, 1000)
SEEDS = 6
STRESS_SEEDS = 3


def _report(label, level, mutation_rate, seeds, start):
    """ Runs one setting over `seeds` and prints its best scores. """
    scores = [evolve.run(population_size=level[0], generations=level[1],
                         mutation_rate=mutation_rate, seed=seed,
                         fitness=competition.competitive_fitness).best_score
              for seed in range(seeds)]
    crossed = sum(1 for score in scores if score >= scaling.optimum())
    print(f'  {label}: max={max(scores)} crossed={crossed}/{seeds} bests={scores}'
          f'  [{time.time() - start:.0f}s]', flush=True)


def main():
    """ Runs the full sweep, printing each setting as it completes. """
    start = time.time()
    print(f'optimum reference = {scaling.optimum()}', flush=True)
    print('== resource scaling (mr=0.5) ==', flush=True)
    for level in RESOURCE_LEVELS:
        _report(f'pop={level[0]} gen={level[1]} budget={level[0] * level[1]}',
                level, 0.5, SEEDS, start)
    print('== mutation-rate sweep (200 x 200) ==', flush=True)
    for mutation_rate in MUTATION_RATES:
        _report(f'mr={mutation_rate}', MUTATION_LEVEL, mutation_rate, SEEDS, start)
    print('== stress ==', flush=True)
    _report(f'pop={STRESS_LEVEL[0]} gen={STRESS_LEVEL[1]}',
            STRESS_LEVEL, 0.5, STRESS_SEEDS, start)
    return 0


if __name__ == '__main__':
    sys.exit(main())
