""" population.py - a minimal Wright-Fisher engine for the K-step waiting time.

The credibility foundation for the whole K-axis apparatus. Before we ever claim
something about how hard it is to build a coordinated K-part structure, we have
to show our evolutionary engine reproduces the results that mainstream population
genetics predicts for the same model. If it does, no one can call the engine
rigged; if it does not, the engine is wrong and we fix it before going on.

The model is deliberately bare:

  - A constant population of `pop_size` asexual replicators.
  - A genome that must complete K sequential steps. `rates[i]` is the
    per-individual per-generation probability of advancing from step i to i+1.
  - A `fitness` per class sets the selection regime. With every intermediate
    NEUTRAL (the default), nothing rewards a half-built structure, so selection
    is blind to progress and only mutation supply and neutral drift can cross the
    gap. That is the honest, hard case, and the regime Durrett and Schmidt (2008)
    solved. With intermediates increasingly fit, there is a GRADIENT and each
    step is selected up as it appears.
  - No back mutation, no recombination.

Two things are validated against closed forms in analytic.py: the neutral
waiting time (mutation and drift) and the fixation probability of a beneficial
mutant (selection). Once both dials match the math, the engine is trusted.

Sampling is pure-stdlib `random` for determinism, matching the rest of the repo.
The binomial sampler steps between successes when a tail is rare (mutation, rare
intermediates) and switches to a normal approximation when both tails are large
(a beneficial class sweeping to high frequency), so every generation stays fast.
"""

import math
import random

DEFAULT_MAX_GENERATIONS = 10 ** 8
_NORMAL_THRESHOLD = 30.0


def _geometric_binomial(trials, prob, rng):
    """ :return: A Binomial(trials, prob) draw by stepping between successes.

    Fast only when the expected count is small; callers route the rarer tail here.
    """
    log_q = math.log1p(-prob)
    count = 0
    index = -1
    while True:
        index += int(math.log(1.0 - rng.random()) / log_q) + 1
        if index >= trials:
            return count
        count += 1


def _binomial(trials, prob, rng):
    """ :return: A Binomial(trials, prob) draw, exact for rare tails.

    Uses a normal approximation only when both expected counts exceed the
    threshold (a diffusion-scale draw, standard in population genetics); otherwise
    it steps between successes on whichever tail is rarer, which stays exact.
    """
    if trials <= 0 or prob <= 0.0:
        return 0
    if prob >= 1.0:
        return trials
    mean = trials * prob
    if mean > _NORMAL_THRESHOLD and trials - mean > _NORMAL_THRESHOLD:
        drawn = int(round(rng.gauss(mean, math.sqrt(mean * (1.0 - prob)))))
        return min(trials, max(0, drawn))
    if prob > 0.5:
        return trials - _geometric_binomial(trials, 1.0 - prob, rng)
    return _geometric_binomial(trials, prob, rng)


def _advance(counts, rates, rng):
    """ :return: New class counts after one generation of mutation.

    Processed from the last step down so a genome advances at most one step per
    generation, matching a low-rate continuous-time process.
    """
    new = list(counts)
    for step in range(len(rates) - 1, -1, -1):
        movers = _binomial(new[step], rates[step], rng)
        new[step] -= movers
        new[step + 1] += movers
    return new


def _reproduce(counts, fitness, pop_size, rng):
    """ :return: New class counts after one Wright-Fisher generation with selection.

    Reproduction is proportional to count times fitness. Drawn as conditional
    binomials from the top class down, with the ground state taking the remainder.
    With uniform fitness this reduces exactly to neutral drift.
    """
    weights = [counts[step] * fitness[step] for step in range(len(counts))]
    new = [0] * len(counts)
    remaining = pop_size
    weight_remaining = sum(weights)
    for step in range(len(counts) - 1, 0, -1):
        if weights[step] == 0.0:
            continue
        drawn = _binomial(remaining, weights[step] / weight_remaining, rng)
        new[step] = drawn
        remaining -= drawn
        weight_remaining -= weights[step]
    new[0] = remaining
    return new


def waiting_time(pop_size, rates, rng, *, fitness=None,
                 max_generations=DEFAULT_MAX_GENERATIONS):
    """ :return: Generations until the first genome completes all K steps.

    K is len(rates). `fitness` is a per-class list of length K+1 (default all
    neutral). Appearance is recorded right after the mutation step, before
    reproduction can lose it. If the budget is exhausted first, returns the budget
    (the structure was not built in time).
    """
    completed = len(rates)
    if fitness is None:
        fitness = [1.0] * (completed + 1)
    counts = [pop_size] + [0] * completed
    generation = 0
    while generation < max_generations:
        generation += 1
        counts = _advance(counts, rates, rng)
        if counts[completed] >= 1:
            return generation
        counts = _reproduce(counts, fitness, pop_size, rng)
    return generation


def mean_waiting_time(pop_size, rates, *, fitness=None, replicates=1000, seed=0,
                      max_generations=DEFAULT_MAX_GENERATIONS):
    # All keyword-only knobs are reported experiment parameters, not hidden state.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """ :return: Mean first-appearance time over independent seeded replicates. """
    rng = random.Random(seed)
    total = 0
    for _ in range(replicates):
        total += waiting_time(pop_size, rates, rng, fitness=fitness,
                              max_generations=max_generations)
    return total / replicates


def fixation_fraction(pop_size, sel, *, replicates=2000, seed=0):
    """ :return: Fraction of runs in which one new (1+sel) mutant fixes.

    Validates the selection dial: one beneficial copy among pop_size neutral ones,
    reproduced under selection with no mutation, run to loss or fixation. The
    fraction that fix is the referee quantity (Haldane/Kimura, about 2*sel).
    """
    rng = random.Random(seed)
    fitness = (1.0, 1.0 + sel)
    fixed = 0
    for _ in range(replicates):
        counts = [pop_size - 1, 1]
        while 0 < counts[1] < pop_size:
            counts = _reproduce(counts, fitness, pop_size, rng)
        if counts[1] == pop_size:
            fixed += 1
    return fixed / replicates
