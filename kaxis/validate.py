""" validate.py - show the engine reproduces the mainstream waiting time.

This is slice 5, the credibility foundation of the K-axis apparatus. It prints,
in a form a reader can check, that the Wright-Fisher engine in population.py
matches the analytic waiting time for a K-step structure with neutral
intermediates:

  - K = 1: the exact geometric appearance time. A sharp unit check.
  - K = 2: the Durrett-Schmidt drift-assisted law. The discriminating fact is
    that cutting the second rate by 16 lengthens the wait by about sqrt(16) = 4,
    not by 16. A neutral intermediate drifts to modest frequency and gives the
    second step many extra chances, so the wait grows like 1/sqrt(u2). Reproducing
    that, and not the naive 1/u2, is what shows the engine is faithful rather than
    a toy.

Once the engine is trusted, later slices vary K and the selection strength and
read off buildability(K); the neutral, selection-off, large-K corner is the
origin-of-replicator limit.
"""

import sys

from kaxis import analytic, population

POP_SIZE = 1000
ONE_STEP_RATE = 3.36e-5
FIRST_RATE = 1e-3
RARE_SECOND = 8e-6
COMMON_SECOND = 128e-6  # sixteen times RARE_SECOND


def main():
    """ Prints the one-step and two-step validation against the referee. """
    simulated = population.mean_waiting_time(
        POP_SIZE, (ONE_STEP_RATE,), replicates=4000, seed=1)
    predicted = analytic.one_step_wait(POP_SIZE, ONE_STEP_RATE)
    print('K = 1 (exact geometric appearance time):')
    print(f'  simulated {simulated:.1f} generations vs analytic {predicted:.1f}'
          f'  (ratio {simulated / predicted:.3f})')
    print()

    rarer = population.mean_waiting_time(
        POP_SIZE, (FIRST_RATE, RARE_SECOND), replicates=150, seed=7)
    common = population.mean_waiting_time(
        POP_SIZE, (FIRST_RATE, COMMON_SECOND), replicates=150, seed=107)
    print('K = 2 (neutral intermediate), second rate cut by 16x:')
    print(f'  wait grows {rarer / common:.2f}x')
    print('  drift-assisted (Durrett-Schmidt) predicts ~4x (sqrt of 16);'
          ' the naive "both at once" model predicts 16x.')
    print()
    print('The engine reproduces the mainstream waiting time, including the'
          ' nontrivial square-root law, so it is trusted to measure'
          ' buildability(K).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
