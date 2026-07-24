""" mutation.py - mutate a protein pool using the observed spectrum.

The point-level spectrum is set to the directly observed human germline numbers,
not anything inferred from phylogeny: roughly 92% single-character substitutions
and 8% small insertions/deletions (the indel rate is ~10-15x below the
substitution rate). Mutations act on the protein source text, so one mutation is
a small change to a multi-step function, the granularity a point mutation has in
a gene.

Whole-protein duplication and deletion (the gene-duplication and gene-loss
analogs) are, in the observed data, far rarer than point events (~0.03% of de
novo mutations). We keep them as separately tunable knobs, deliberately elevated
above that observed frequency so their effect can be studied at all, and we say
so rather than hide it.

The absolute per-division rate is a tunable knob and is scaled up from biology's
per-base rate, because we cannot run biology's population sizes or timescales.
What is calibrated to biology is the relative spectrum, not the absolute rate.
"""

import math
import string

from protocell.protein import Protein

# Characters a substitution or insertion may introduce: enough of Python's
# alphabet to explore code, matching the source the proteins are written in.
ALPHABET = string.ascii_letters + string.digits + " ()[]{}:,.+-*/<>=%_'\n"

# Observed germline point spectrum.
SUBSTITUTION_SHARE = 0.92
INSERTION_SHARE = 0.04  # the remaining 0.08 is split between the two indel types
# (deletion is whatever is left)

DEFAULT_POINT_LAMBDA = 1.0
DEFAULT_DUPLICATION_RATE = 0.03
DEFAULT_PROTEIN_DELETION_RATE = 0.03


def _poisson(lam, rng):
    """ :return: A Poisson(lam) sample using Knuth's method """
    target = math.exp(-lam)
    count, product = 0, 1.0
    while True:
        count += 1
        product *= rng.random()
        if product <= target:
            return count - 1


def _point_mutate(source, rng):
    """ Applies one point event to source text, by the observed spectrum. """
    if not source:
        return rng.choice(ALPHABET)
    position = rng.randrange(len(source))
    roll = rng.random()
    if roll < SUBSTITUTION_SHARE:
        return source[:position] + rng.choice(ALPHABET) + source[position + 1:]
    if roll < SUBSTITUTION_SHARE + INSERTION_SHARE:
        return source[:position] + rng.choice(ALPHABET) + source[position:]
    return source[:position] + source[position + 1:]


def mutate(proteins, rng, *, point_lambda=DEFAULT_POINT_LAMBDA,
           duplication_rate=DEFAULT_DUPLICATION_RATE,
           protein_deletion_rate=DEFAULT_PROTEIN_DELETION_RATE):
    """ Returns a mutated copy of a protein pool.

        Structural events first (rare): a whole protein may be duplicated or
        deleted. Then a Poisson-distributed number of point events, each a
        substitution, insertion, or deletion in one protein's source at the
        observed relative rates.
    :param proteins: The parent pool (a list of Proteins)
    :param rng: A random.Random, for reproducibility
    :return: A new list of Proteins
    """
    pool = list(proteins)
    if pool and rng.random() < duplication_rate:
        index = rng.randrange(len(pool))
        pool.insert(index, Protein(pool[index].source))
    if len(pool) > 1 and rng.random() < protein_deletion_rate:
        del pool[rng.randrange(len(pool))]
    for _ in range(_poisson(point_lambda, rng)):
        if not pool:
            break
        index = rng.randrange(len(pool))
        pool[index] = Protein(_point_mutate(pool[index].source, rng))
    return pool
