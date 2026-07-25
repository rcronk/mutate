""" analytic.py - the mainstream waiting-time predictions we validate against.

These are the referee. The simulation in population.py is only trusted to the
extent it reproduces these closed forms for the same model.

  - one_step_wait: with a single step, first appearance is geometric in the
    per-generation success probability across the whole population. This is exact,
    so it is the sharp unit test on the engine's mutation supply and timing.

  - two_step_wait: Durrett and Schmidt (2008), "Waiting for Two Mutations",
    Genetics 180:1501. With a NEUTRAL intermediate, the mean wait for both steps
    in one lineage is about 1 / (2 N u1 sqrt(u2)). The square root is the whole
    result: a neutral intermediate can drift to modest frequency and give the
    second step many more chances than a "both at once" model would allow, so the
    wait grows like 1/sqrt(u2), not 1/u2. Valid when u2 << 1/N.
"""

import math


def one_step_wait(pop_size, rate):
    """ :return: Exact mean generations to the first single-step genome. """
    appearance_prob = 1.0 - (1.0 - rate) ** pop_size
    return 1.0 / appearance_prob


def two_step_wait(pop_size, rate1, rate2):
    """ :return: Durrett-Schmidt mean wait for two steps, neutral intermediate.

    Approximation; assumes rate2 << 1 / pop_size (the drift-assisted regime).
    """
    return 1.0 / (2.0 * pop_size * rate1 * math.sqrt(rate2))


def fixation_probability(pop_size, sel):
    """ :return: Kimura's fixation probability of one new (1+sel) mutant.

    (1 - e^-2s) / (1 - e^-2Ns) for a single copy at frequency 1/N. About 2*sel
    when sel is small and N*sel is large (Haldane). This is the referee for the
    selection dial.
    """
    if sel == 0.0:
        return 1.0 / pop_size
    return (1.0 - math.exp(-2.0 * sel)) / (1.0 - math.exp(-2.0 * pop_size * sel))
