""" substrate.py - the mutable Python-program substrate for Option 3.

Option 3 asks whether mutation and selection can build functional complexity in a
self-modifying Python program held to a substrate no more forgiving than biology.
The program is a creature genome: Python source defining act(). This module is
the thin substrate layer, reusing creatures.genome: the ancestor, one single
mutation, and a functional/behaviour evaluation.

Functional here is the same survival bar biology's tolerance was measured
against in ridge.dfe: the source parses, defines act(), and runs without error on
a fixed grid of input contexts. It says nothing about the quality of the
behaviour, only that the program does not crash. Two functional programs that
return the same decision on every context have the same behaviour; a mutation
that changes any decision changed behaviour.
"""

import itertools

from creatures import genome

ANCESTOR = genome.ANCESTOR_SOURCE

# A systematic grid of input contexts, so a mutation that changes behaviour on
# any input is detected, not just on a lucky few. max_fuel is the fixed ceiling;
# the other four senses are swept across low, middle and high values.
_AGES = (0, 2, 5)
_FUELS = (1, 5, 9)
_FOODS = (0, 10, 100)
_POPULATIONS = (1, 10)
CONTEXTS = tuple(
    {'age': age, 'fuel': fuel, 'max_fuel': 10,
     'food_available': food, 'population': population}
    for age, fuel, food, population
    in itertools.product(_AGES, _FUELS, _FOODS, _POPULATIONS))


def evaluate(source):
    """ Runs a program across every context and returns its behaviour.
    :param source: Candidate program source
    :return: A hashable behaviour fingerprint (the decisions on every context),
        or None if the program is not functional
    """
    if not genome.is_viable(source):
        return None
    try:
        return tuple(tuple(sorted(genome.decide(source, **context).items()))
                     for context in CONTEXTS)
    except genome.MisbehavingCreatureError:
        return None


def is_functional(source):
    """ :return: True if the source parses, defines act(), and runs everywhere """
    return evaluate(source) is not None


def mutate_once(source, seed):
    """ :return: One single mutation of the source, deterministic for a seed """
    return genome.mutate_source(source, seed)
