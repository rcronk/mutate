""" gb1.py - loads the GB1 four-site protein landscape for path analysis.

The beta-lactamase landscape in dms.py is binary: each of five mutations is
present or absent. GB1 is different in shape. It measures the binding fitness of
every combination of twenty amino acids at four sites of an antibody-binding
protein domain, so a genotype is a four-letter amino-acid string (wild type is
VDGV) rather than a bit vector.

That richer alphabet is why GB1 is a stronger second data point than
beta-lactamase. Instead of one wild-type-to-peak path it holds a whole rugged
landscape with many peaks, so we can ask the accessibility question many times
and get a distribution, not a single answer. This is the same question Part B
asks of one real protein, scaled up to many peaks in one protein, and it is the
shape Option 2's origin-of-new-function data will also take.

To reuse paths.accessible_paths unchanged, `pair_fitness` reduces a chosen
start-to-target pair back to the binary form the analyzer expects: at each site
where start and target differ, bit 0 means the start's amino acid and bit 1
means the target's, so an all-zero-to-all-one walk over k bits is exactly the
set of direct paths between those two real genotypes.
"""

import csv
import dataclasses
import itertools

WILD_TYPE = 'VDGV'
_STANDARD_AA = set('ACDEFGHIKLMNPQRSTVWY')


@dataclasses.dataclass
class Gb1Landscape:
    """ Measured binding fitness for each four-amino-acid genotype. """
    values: dict
    wild_type: str = WILD_TYPE

    def fitness(self, variant):
        """ Looks up the measured fitness of a variant.
        :param variant: A four-letter amino-acid string
        :return: The measured fitness
        :raises KeyError: if the variant was not measured
        """
        return self.values[variant]

    def neighbours(self, variant):
        """ Yields the measured single-substitution neighbours of a variant.
            A neighbour changes exactly one of the four sites to another of the
            twenty amino acids and is present in the data.
        :return: An iterator of neighbour strings
        """
        for site, current in enumerate(variant):
            for amino in _STANDARD_AA:
                if amino != current:
                    candidate = variant[:site] + amino + variant[site + 1:]
                    if candidate in self.values:
                        yield candidate

    def local_maxima(self):
        """ Finds every variant fitter than all of its measured neighbours.
            These are the peaks of the landscape; their count measures how
            rugged it is. A single smooth hill would have one.
        :return: A sorted list of peak variants
        """
        peaks = [variant for variant, score in self.values.items()
                 if all(score > self.fitness(nb) for nb in self.neighbours(variant))]
        return sorted(peaks)

    def is_complete_cube(self, start, target):
        """ True if every genotype between start and target is measured.
            The k differing sites span a k-dimensional cube of 2**k genotypes;
            accessibility over all k! direct paths is only defined when the
            whole cube is present.
        :return: Whether all intermediate genotypes exist in the data
        """
        differing = [i for i in range(len(start)) if start[i] != target[i]]
        for bits in itertools.product((0, 1), repeat=len(differing)):
            if self._genotype(start, target, differing, bits) not in self.values:
                return False
        return True

    def pair_fitness(self, start, target):
        """ Reduces a start-to-target pair to the binary form paths expects.
            At each differing site, bit 0 is the start's amino acid and bit 1 is
            the target's, so the all-zero-to-all-one walk is the set of direct
            paths from start to target.
        :return: (fitness callable over k-bit tuples, k), where k is the number
            of differing sites
        :raises KeyError: from the callable if an intermediate is not measured
        """
        differing = [i for i in range(len(start)) if start[i] != target[i]]

        def fitness(bits):
            return self.values[self._genotype(start, target, differing, bits)]

        return fitness, len(differing)

    @staticmethod
    def _genotype(start, target, differing, bits):
        """ Builds the genotype string for a point on the start-target cube. """
        chars = list(start)
        for site, bit in zip(differing, bits):
            chars[site] = target[site] if bit else start[site]
        return ''.join(chars)


def load_gb1_landscape(path, *, variant_column='variant', fitness_column='fitness'):
    """ Loads the GB1 four-site landscape from a CSV.
    :param path: Path to the CSV
    :param variant_column: Name of the column holding the amino-acid string
    :param fitness_column: Name of the column holding fitness
    :return: A Gb1Landscape
    :raises ValueError: if a required column is absent
    """
    with open(path, encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    if not rows or variant_column not in rows[0] or fitness_column not in rows[0]:
        raise ValueError(f'need columns {variant_column!r} and {fitness_column!r} '
                         f'in {path}')
    values = {row[variant_column]: float(row[fitness_column]) for row in rows}
    return Gb1Landscape(values=values)


def static_hamming(start, target):
    """ :return: Number of sites at which two equal-length strings differ """
    return sum(a != b for a, b in zip(start, target))
