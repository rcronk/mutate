""" landscape.py - a fitness landscape whose ridge/gap structure is tunable.

A genome is a sequence of N binary parts. The target is all-correct (all 1s).
The landscape splits into two regions:

  - The first N-g parts are *reducible*: each correct part adds 1 to fitness on
    its own, forming a ridge that selection can climb one step at a time.

  - The last g parts are an *irreducible block*: they pay a bonus of g, but only
    when all g are correct at once.

g is the coordination degree, the single quantity this experiment exists to
vary, because the claim under test is that evolvability is set by g (the gap),
not by N (how many parts the target has).

There is a second, subtler dial: what a *half-built* block is worth. It turns
out to matter more than g itself.

  - valley_depth = 0: a half-built block is worth nothing, the same as an empty
    one. The gap is *neutral*. A population can wander across it by drift,
    exploring the 2^g block configurations at no cost, so even a fairly wide
    neutral gap gets crossed. Evolution handles these.

  - valley_depth > 0: each part added to an incomplete block *lowers* fitness,
    as a half-built machine that costs resources and does nothing would. The gap
    is now a *valley*: selection actively pushes the block back toward empty, so
    the only way across is to complete all g parts in a single leap against the
    gradient. This is the real irreducible-complexity barrier, and it is
    exponentially harder than a neutral gap of the same width.

The honest lesson, which the tests forced out: "is there a gap" is the wrong
question. "Is the gap neutral or deleterious" is the one that decides whether
cumulative selection can cross it.
"""


class Landscape:
    """ A tunable ridge-then-gap fitness function over binary genomes. """

    def __init__(self, n_parts, coordination_degree, valley_depth=0):
        if not 1 <= coordination_degree <= n_parts:
            raise ValueError(
                f'coordination_degree must be in [1, {n_parts}], '
                f'got {coordination_degree}')
        if valley_depth < 0:
            raise ValueError(f'valley_depth must be >= 0, got {valley_depth}')
        self.n_parts = n_parts
        self.coordination_degree = coordination_degree
        self.valley_depth = valley_depth
        self.reducible = n_parts - coordination_degree

    def fitness(self, genome):
        """ Scores a genome.

            Ridge: one point per correct reducible part. Completed block: the
            full bonus of g. Incomplete block: a penalty of valley_depth per
            part already placed, which is zero when valley_depth is zero (a
            neutral gap) and a downhill slope otherwise (a deleterious valley).
        :param genome: A sequence of 0/1 of length n_parts
        :return: Fitness
        """
        if len(genome) != self.n_parts:
            raise ValueError(f'expected {self.n_parts} parts, got {len(genome)}')
        ridge = sum(genome[:self.reducible])
        block = genome[self.reducible:]
        if all(block):
            return ridge + self.coordination_degree
        return ridge - self.valley_depth * sum(block)

    @property
    def max_fitness(self):
        """ :return: The fitness of the completed target """
        return self.n_parts

    def is_optimal(self, genome):
        """ :return: True if the genome is the completed target """
        return self.fitness(genome) == self.max_fitness
