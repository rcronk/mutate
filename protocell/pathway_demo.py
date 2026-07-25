""" pathway_demo.py - a readable view of the K-axis result.

Slices 5 to 7 established, and validated against mainstream population genetics,
that building a K-part coordinated structure is cheap when a gradient of rewarded
intermediates exists and stalls when it does not. That is a curve. This is the
same thing you can read: the genome is real protein source, so you can look at a
run and SEE whether the structure got built, not only trust a number.

A cell builds a metabolic pathway of up to K enzymes. Each enzyme is one readable
protein in the pool, so a half-built pathway is a real, runnable genome (the
pool-of-proteins substrate gives partial credit for free: one missing enzyme does
not break the others). Two chemistries set the regime:

  - GRADIENT: every working enzyme helps a little (fitness rises with the count),
    so a partial pathway is rewarded.
  - NO GRADIENT: the pathway yields nothing until all K enzymes are present, so no
    intermediate is rewarded.

Honesty note: this is a readable ILLUSTRATION of the kaxis result, not new
evidence. Each enzyme is gained or lost as a unit, matching the one-mutation-per-
step model the apparatus validated. It deliberately does NOT model assembling an
enzyme character by character from scratch, which is a separate and harder problem
(code-space is far more rugged than this) and would only make building less
likely, not more. What it isolates and shows is the gradient effect.

Run: python -m protocell.pathway_demo
"""

import random
import sys

from protocell.cell import Cell
from protocell.protein import Protein

ENZYME_NAMES = ('oxidase', 'reductase', 'synthase', 'ligase', 'kinase',
                'hydrolase', 'isomerase', 'transferase')


def _enzyme_source(name):
    """ :return: Readable source for one enzyme protein that advances the pathway. """
    return f'def protein(cell, env):\n    cell.registers[0] += 1  # {name}\n'


def render_genome(active):
    """ :return: The active enzymes as real, readable protein source objects. """
    return [Protein(_enzyme_source(ENZYME_NAMES[index])) for index in sorted(active)]


def working_enzymes(genome):
    """ :return: How many enzymes actually run, by executing the real proteins. """
    cell = Cell(genome)
    for protein in genome:
        protein.execute(cell, None)
    return cell.registers[0]


def fitness(active, coordination, *, gradient):
    """ :return: Fitness of a genome under the chosen chemistry. """
    made = len(active)
    if gradient:
        return made
    return coordination if made >= coordination else 0


def _mutate(active, coordination, rng, *, birth, loss):
    """ :return: The genome after per-gene chances of gaining or losing an enzyme.

    Per gene, so that without a reward births and losses balance at a sparse
    genome; only selection (or, rarely, drift) fills it. This is what keeps the
    no-gradient case honest rather than letting mutation pressure build it.
    """
    active = set(active)
    for index in range(coordination):
        if index in active:
            if rng.random() < loss:
                active.discard(index)
        elif rng.random() < birth:
            active.add(index)
    return active


def evolve(coordination, *, gradient, pop_size=200, generations=350,
           birth=0.006, loss=0.055, seed=0):
    # The knobs are reported experiment parameters, not hidden state.
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """ :return: The fittest genome (set of enzyme indices) after selection. """
    rng = random.Random(seed)
    population = [set() for _ in range(pop_size)]
    for _ in range(generations):
        weights = [fitness(genome, coordination, gradient=gradient) + 1
                   for genome in population]
        chosen = rng.choices(population, weights=weights, k=pop_size)
        population = [_mutate(genome, coordination, rng, birth=birth, loss=loss)
                      for genome in chosen]
    return max(population,
               key=lambda genome: (fitness(genome, coordination, gradient=gradient),
                                   len(genome)))


def build_fraction(coordination, *, gradient, trials=20, **knobs):
    """ :return: Fraction of runs that build the full K-enzyme pathway. """
    return sum(1 for seed in range(trials)
               if len(evolve(coordination, gradient=gradient, seed=seed, **knobs))
               == coordination) / trials


def main():
    """ Prints the buildability contrast and dumps an evolved genome to read. """
    print('Building a K-enzyme pathway: fraction of runs that finish it,')
    print('gradient chemistry (partial pathway rewarded) vs no gradient:')
    print(f"  {'K':>2}  {'gradient':>9}  {'no gradient':>12}")
    for coordination in range(2, 7):
        with_gradient = build_fraction(coordination, gradient=True)
        without = build_fraction(coordination, gradient=False)
        print(f'  {coordination:>2}  {with_gradient:>9.0%}  {without:>12.0%}')
    print()
    example = 6
    built = evolve(example, gradient=True, seed=0)
    stalled = evolve(example, gradient=False, seed=0)
    print(f'What a run actually builds at K={example}, as readable protein source:')
    print(f'  WITH a gradient ({len(built)}/{example} enzymes, runs to '
          f'{working_enzymes(render_genome(built))}):')
    print(_indent(render_genome(built)))
    print(f'  WITHOUT a gradient ({len(stalled)}/{example} enzymes, runs to '
          f'{working_enzymes(render_genome(stalled))}):')
    print(_indent(render_genome(stalled)) or '    (nothing was built)')
    return 0


def _indent(genome):
    """ :return: The genome's proteins as indented readable source. """
    return '\n'.join('    ' + line for protein in genome
                     for line in protein.source.strip().splitlines())


if __name__ == '__main__':
    sys.exit(main())
