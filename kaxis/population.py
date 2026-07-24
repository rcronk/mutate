""" population.py - a minimal Wright-Fisher engine for the K-step waiting time.

The credibility foundation for the whole K-axis apparatus. Before we ever claim
something about how hard it is to build a coordinated K-part structure, we have
to show our evolutionary engine reproduces the waiting time that mainstream
population genetics predicts for the same model. If it does, no one can call the
engine rigged; if it does not, the engine is wrong and we fix it before going on.

The model is deliberately bare:

  - A constant population of `pop_size` asexual replicators.
  - A genome that must complete K sequential steps. `rates[i]` is the
    per-individual per-generation probability of advancing from step i to i+1.
  - Every intermediate (0..K-1 steps done) is selectively NEUTRAL. Only the
    finished K-step genome is "the structure"; we time its first appearance.
  - No back mutation, no recombination.

Neutral intermediates are the honest, hard case: nothing rewards a half-built
structure, so selection is blind to the intermediates and the only forces are
mutation supply and neutral drift. That is exactly the regime Durrett and Schmidt
(2008) solved analytically, which is our referee in analytic.py.

Sampling is pure-stdlib `random` for determinism, matching the rest of the repo.
Both the mutation step and the drift resample act only on rare classes (the
intermediates are always a small minority in this regime), so a geometric-gap
binomial sampler keeps every draw fast.
"""

import math
import random

DEFAULT_MAX_GENERATIONS = 10 ** 8


def _binomial(trials, prob, rng):
    """ :return: An exact Binomial(trials, prob) draw via geometric gap skipping.

    Fast when prob is small (the regime here), because it steps from one success
    to the next rather than testing every trial.
    """
    if trials <= 0 or prob <= 0.0:
        return 0
    if prob >= 1.0:
        return trials
    log_q = math.log1p(-prob)
    count = 0
    index = -1
    while True:
        gap = int(math.log(1.0 - rng.random()) / log_q)
        index += gap + 1
        if index >= trials:
            return count
        count += 1


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


def _drift(counts, pop_size, rng):
    """ :return: New class counts after one neutral Wright-Fisher resample.

    Drawn as conditional binomials over the rare intermediate classes; the
    ground state (step 0) takes the remainder, so every binomial draw has a small
    probability and stays fast.
    """
    new = [0] * len(counts)
    remaining = pop_size
    prob_remaining = 1.0
    for step in range(len(counts) - 1, 0, -1):
        if counts[step] == 0:
            continue
        prob = counts[step] / pop_size
        drawn = _binomial(remaining, prob / prob_remaining, rng)
        new[step] = drawn
        remaining -= drawn
        prob_remaining -= prob
    new[0] = remaining
    return new


def waiting_time(pop_size, rates, rng, *, max_generations=DEFAULT_MAX_GENERATIONS):
    """ :return: Generations until the first genome completes all K steps.

    K is len(rates). Appearance is recorded right after the mutation step, before
    drift can lose it, matching "time until some individual has experienced all
    the mutations."
    """
    completed = len(rates)
    counts = [pop_size] + [0] * completed
    generation = 0
    while generation < max_generations:
        generation += 1
        counts = _advance(counts, rates, rng)
        if counts[completed] >= 1:
            return generation
        counts = _drift(counts, pop_size, rng)
    return generation


def mean_waiting_time(pop_size, rates, *, replicates=1000, seed=0,
                      max_generations=DEFAULT_MAX_GENERATIONS):
    """ :return: Mean first-appearance time over independent seeded replicates. """
    rng = random.Random(seed)
    total = 0
    for _ in range(replicates):
        total += waiting_time(pop_size, rates, rng, max_generations=max_generations)
    return total / replicates
