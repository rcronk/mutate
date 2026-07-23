""" dfe.py - the distribution of fitness effects, measured from real landscapes.

This is the calibration target for the simulation. Before asking how much
functional complexity mutation and selection can build in a Python substrate, we
have to know how forgiving real molecules are, so we can make the substrate no
more forgiving and no less.

Forgiveness here is about survival, not marginal fitness. Starting from a working
genotype, a single mutation either keeps it working (tolerated) or breaks it
(disruptive). That split is scale-free, so it is comparable across landscapes whose
fitness is measured in different units, and it is the quantity a substrate's
mutation tolerance must be dialled to match. Among the tolerated mutations we
also count how many actually improve fitness (beneficial), the raw material
selection has to work with.

The DFE is measured *from functional backgrounds*, not from all genotypes. The
effect of a mutation depends entirely on where you start: from a broken genotype
almost anything is neutral or better, from a working one most changes hurt. Only
the second question calibrates a substrate, so a background counts only if it is
at least as fit as the functional threshold (the wild type by default).
"""

import dataclasses
import statistics


@dataclasses.dataclass
class Dfe:
    """ The survival split of single mutations from functional backgrounds. """
    tolerated: int
    disruptive: int
    beneficial: int
    median_deleterious_effect: float

    @property
    def total(self):
        """ :return: How many single-mutation steps were measured """
        return self.tolerated + self.disruptive

    @property
    def fraction_tolerated(self):
        """ :return: Share of mutations that keep the genotype functional, the
            forgiveness the substrate must match (0 with no data) """
        return self.tolerated / self.total if self.total else 0.0

    @property
    def fraction_disruptive(self):
        """ :return: Share of mutations that drop below the functional
            threshold (0 with no data) """
        return self.disruptive / self.total if self.total else 0.0

    @property
    def fraction_beneficial(self):
        """ :return: Share of mutations that improve fitness (0 with no data) """
        return self.beneficial / self.total if self.total else 0.0


def measure(values, neighbours_of, *, functional_threshold):
    """ Measures the DFE from every functional background in a landscape.

        A background is functional if its fitness is at least
        functional_threshold. Each of its measured single-mutation neighbours is
        one step: tolerated if the neighbour is still at or above the threshold,
        otherwise disruptive, and additionally beneficial if the neighbour is fitter
        than the background.
    :param values: A dict from genotype to fitness
    :param neighbours_of: A callable from a genotype to its measured single-
        mutation neighbours
    :param functional_threshold: Minimum fitness for a genotype to be functional
    :return: A Dfe
    """
    tolerated = disruptive = beneficial = 0
    deleterious_effects = []
    for parent, parent_fitness in values.items():
        if parent_fitness < functional_threshold:
            continue
        for child in neighbours_of(parent):
            child_fitness = values[child]
            if child_fitness >= functional_threshold:
                tolerated += 1
                if child_fitness > parent_fitness:
                    beneficial += 1
                else:
                    deleterious_effects.append(parent_fitness - child_fitness)
            else:
                disruptive += 1
    median = statistics.median(deleterious_effects) if deleterious_effects else 0.0
    return Dfe(tolerated=tolerated, disruptive=disruptive, beneficial=beneficial,
               median_deleterious_effect=median)


def measure_landscape(land, *, functional_threshold=None):
    """ Measures the DFE of a four-site landscape from its functional core.

        Convenience wrapper for a Gb1Landscape-shaped object: its `values` dict
        and `neighbours` method, with the wild-type fitness as the default
        functional threshold.
    :param land: An object with `.values`, `.neighbours`, `.wild_type`, `.fitness`
    :return: A Dfe
    """
    if functional_threshold is None:
        functional_threshold = land.fitness(land.wild_type)
    return measure(land.values, land.neighbours,
                   functional_threshold=functional_threshold)
