""" genome.py - the mutable part of a creature.

A creature is Python source text holding one function, act(), which decides how
much food to request and whether to reproduce. That is all it owns. Aging,
fuel accounting and death live in lifecycle.py, where mutation cannot reach
them, so a creature cannot evolve its way out of dying.

Mutants are checked with ast.parse before anything is spawned, so a syntax
error costs a parse rather than a forked process. Semantic errors pass the gate
and kill the creature at runtime, which is the part worth watching.

A child's seed derives from its parent's seed and its birth index. Process
scheduling is nondeterministic, so a run cannot be reproduced byte for byte,
but genetics can: the same founder seed and the same birth indices always
produce the same genomes.
"""

import ast
import contextlib
import hashlib
import io
import random
import sys
import os
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'legacy'))

import mutate  # noqa: E402  pylint: disable=wrong-import-position

# Deliberately minimal, but it now perceives the world and makes a life-history
# choice, so mutation has a real strategy landscape to explore rather than four
# lines to break.
#
# It senses two things beyond its own state: how much food is in the shared pool
# and how many creatures are alive. It makes three choices: how much to eat,
# whether to try to breed, and how much of its own fuel to endow each offspring.
# The endowment is the evolvable r/K dial: many cheap offspring that start poor,
# or few well-provisioned ones.
#
# What it still does NOT do is police its own fertility. An earlier version
# hardcoded `2 <= age <= 5`, which capped every creature at two breeding
# attempts regardless of the engine's fertile window and drove every population
# extinct. Fertility is the engine's business (lifecycle.can_reproduce); the
# creature just asks.
ANCESTOR_SOURCE = '''def act(age, fuel, max_fuel, food_available, population):
    hungry = fuel < max_fuel / 2
    scarce = food_available < population
    return {
        'eat': 6 if (hungry or scarce) else 3,
        'reproduce': not hungry,
        'endowment': fuel // 4,
    }
'''

class MisbehavingCreatureError(Exception):
    """ Raised when a creature's act() cannot be called or returns nonsense. """


def is_viable(source):
    """ The spawn gate: can this source be parsed and does it define act()?

        Cheap by design. Rejecting a syntax error here costs a parse instead of
        a forked process.
    :param source: Candidate Python source
    :return: True if the source is worth spawning
    """
    try:
        # Mutants also trigger warnings at parse time, such as invalid decimal
        # literals, not only at exec time.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    return any(isinstance(node, ast.FunctionDef) and node.name == 'act'
               for node in tree.body)


def load(source):
    """ Executes the source and returns its act() function.
    :param source: Creature source
    :return: The act callable
    """
    namespace = {}
    try:
        # Mutants routinely produce constructs Python warns about, such as `is`
        # with a literal. Left unsuppressed these flood stderr: one exploratory
        # run emitted 64,523 warning lines. They are expected output of a
        # mutation experiment, not a problem to report.
        # redirect_stdout so a mutant that grew a print() cannot pollute our
        # output; one exploratory run turned into pages of stray True/False.
        with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
            warnings.simplefilter('ignore')
            exec(source, namespace)  # pylint: disable=exec-used
    except Exception as error:  # pylint: disable=broad-except
        raise MisbehavingCreatureError(f'source failed to execute: {error}') from error
    act = namespace.get('act')
    if not callable(act):
        raise MisbehavingCreatureError('source does not define a callable act()')
    return act


# Five sense inputs a creature conditions on, all keyword-only. The count
# reflects how much of the world a creature can perceive, not a design problem.
def decide(source, *, age, fuel, max_fuel,  # pylint: disable=too-many-arguments
           food_available, population):
    """ Asks a creature what it wants to do, and never trusts the answer.

        A mutant can return anything at all, so the result is normalised: missing
        keys take defaults, and every numeric field is clamped into range with
        anything non-numeric becoming zero. A creature that raises, returns a
        non-dict, or no longer accepts the full call is reported as misbehaving
        rather than allowed to corrupt the world.
    :param source: Creature source
    :param age: Current age in ticks
    :param fuel: Current fuel
    :param max_fuel: The creature's fuel ceiling
    :param food_available: Food in the shared pool this tick
    :param population: How many creatures are alive
    :return: dict with 'eat' (int), 'reproduce' (bool), 'endowment' (int)
    """
    act = load(source)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            raw = act(age, fuel, max_fuel, food_available, population)
    except Exception as error:  # pylint: disable=broad-except
        raise MisbehavingCreatureError(f'act() raised: {error}') from error

    if not isinstance(raw, dict):
        raise MisbehavingCreatureError(f'act() returned {type(raw).__name__}, expected dict')

    return {'eat': _clamp(raw.get('eat', 0), max_fuel),
            'reproduce': bool(raw.get('reproduce', False)),
            'endowment': _clamp(raw.get('endowment', 0), max_fuel)}


def _clamp(value, ceiling):
    """ Forces a numeric decision field into [0, ceiling].
    :param value: Whatever the creature asked for
    :param ceiling: Upper bound
    :return: An integer between 0 and ceiling
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    try:
        wanted = int(value)
    except (ValueError, OverflowError):
        return 0
    return max(0, min(wanted, ceiling))


def mutate_source(source, seed):
    """ Produces one mutant of the given source.

        Uses the same six operators as the legacy experiments, including the
        deletion and duplication added in #16, so genomes here are not
        restricted to growing the way the 2016 ones were.
    :param source: Parent source
    :param seed: Random seed; the same seed always gives the same mutant
    :return: Mutated source
    """
    random.seed(seed)
    return mutate.Creature._flawed_copy(source)  # pylint: disable=protected-access


def derive_seed(parent_seed, birth_index):
    """ Derives a child's seed from its parent's seed and birth index.

        Hashed rather than added so sibling seeds are not adjacent, which would
        otherwise correlate siblings' mutations.
    :param parent_seed: The parent's seed
    :param birth_index: Which offspring this is, counting from zero
    :return: A new seed
    """
    digest = hashlib.sha256(f'{parent_seed}:{birth_index}'.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], 'big')


class Genome:
    """ One creature's heritable material and its place in the lineage. """

    def __init__(self, source, seed, identity, generation):
        self.source = source
        self.seed = seed
        self.identity = identity
        self.generation = generation

    @classmethod
    def founder(cls, seed, identity='0'):
        """ Creates a founding creature of a run.

            Each founder needs its own identity. When several founders shared
            the identity '0', every lineage in the event log appeared to
            descend from the same creature and per-creature tracking silently
            collapsed.
        :param seed: Founder seed for this lineage
        :param identity: Lineage root, unique per founder
        :return: A Genome carrying the unmutated ancestor
        """
        return cls(ANCESTOR_SOURCE, seed, identity=identity, generation=1)

    def child(self, birth_index, mutation_probability=1.0):
        """ Attempts one offspring. The attempt may fail.

            Exactly one mutation is tried. If the result cannot be parsed, the
            birth fails and None is returned. It is deliberately not retried:
            retrying until something valid appears would hide the brittleness
            of the substrate, which is the quantity this project exists to
            measure, and no organism gets unlimited attempts at one birth.

            Passing the parse gate is not the same as being alive. About 69% of
            mutants that parse still crash when called, and those die in the
            world rather than here, so the cause of death is recorded honestly.
        :param birth_index: Which offspring this is, counting from zero
        :param mutation_probability: Chance this offspring is mutated at all.
            At 1.0 every birth mutates, which is a rate of one mutation per
            genome per generation. For a genome of a few hundred bytes with no
            redundancy that is far above any biological rate, and it drives the
            population past the error threshold: damage accumulates faster than
            selection can remove it and the lineage melts down. Below the
            threshold most offspring are faithful copies and variation still
            arrives, just slowly enough to be selected on.
        :return: A new Genome, or None if the mutant could not be parsed
        """
        seed = derive_seed(self.seed, birth_index)
        identity = f'{self.identity}.{birth_index}'

        # The mutate-or-not coin and the mutation itself must use independent
        # seeds. Reusing one seed for both correlates them: when the coin only
        # fires for seeds whose first random() is below the probability, and the
        # mutation then reseeds with that same value, _flawed_copy's first draw
        # is forced into the same low range and always selects the first
        # operator (prepend). At mutation_probability 0.1 that made 97% of
        # mutants unparseable, since prepending to `def act(...)` breaks the
        # parse almost every time.
        if random.Random(seed).random() >= mutation_probability:
            return Genome(source=self.source, seed=seed, identity=identity,
                          generation=self.generation + 1)

        candidate = mutate_source(self.source, derive_seed(seed, 'mutation'))
        if not is_viable(candidate):
            return None
        return Genome(source=candidate, seed=seed, identity=identity,
                      generation=self.generation + 1)
