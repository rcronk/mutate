""" dms.py - loads real mutational-scanning landscapes for path analysis.

A binary landscape is a fitness value attached to each combination of k
mutations, each present (1) or absent (0). That is the same shape as Part A's
synthetic genome and the same shape `paths.accessible_paths` expects, so a real
protein's measured landscape drops straight into the analyzer we validated on
Part A.

The loader reads a CSV whose first columns are the k mutation flags (0/1) and
which has a named fitness column. The Weinreich et al. (2006) beta-lactamase
data in data/ is exactly this: five mutation columns plus an MIC column.
"""

import csv
import dataclasses


@dataclasses.dataclass
class BinaryLandscape:
    """ A measured fitness value for each k-bit genotype. """
    k: int
    values: dict

    def fitness(self, genotype):
        """ Looks up the measured fitness of a genotype.
        :param genotype: A tuple of k 0/1 values
        :return: The measured fitness
        :raises KeyError: if the genotype was not measured
        """
        return self.values[tuple(genotype)]


def load_binary_landscape(path, *, fitness_column):
    """ Loads a binary combinatorial landscape from a CSV.

        Every column before the fitness column is treated as a mutation flag,
        read as 0/1. This matches the layout of the Weinreich data: the mutation
        columns come first, then MIC and log_MIC.
    :param path: Path to the CSV
    :param fitness_column: Name of the column holding fitness
    :return: A BinaryLandscape
    :raises ValueError: if the fitness column is absent
    """
    with open(path, encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    if not rows or fitness_column not in rows[0]:
        raise ValueError(f'no column {fitness_column!r} in {path}')

    flag_columns = [name for name in rows[0]
                    if name != fitness_column and _looks_like_flag(rows, name)]
    values = {}
    for row in rows:
        genotype = tuple(int(row[name]) for name in flag_columns)
        values[genotype] = float(row[fitness_column])
    return BinaryLandscape(k=len(flag_columns), values=values)


def _looks_like_flag(rows, column):
    """ :return: True if every value in the column is 0 or 1 """
    try:
        return all(row[column].strip() in ('0', '1') for row in rows)
    except (KeyError, AttributeError):
        return False
