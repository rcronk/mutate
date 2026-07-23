""" steroid.py - loads the ancestral steroid-receptor landscape.

Beta-lactamase and GB1 are optimisation landscapes: an enzyme that already works
is tuned to work better. This is different. AncSR1 is a reconstructed ancestral
transcription factor whose recognition helix EGKA binds one DNA element (ERE)
and is null on another (SRE). SRE binding is a genuinely new function that
appeared later in a sibling lineage. So this landscape lets Part B ask the
question that matters most for the whole project: is the path to a function that
did not exist before a crossable ridge or a valley?

The recognition helix is four amino-acid sites, exactly the shape of the GB1
landscape, so the same Gb1Landscape and the same paths.accessible_paths run on
it unchanged. What is new here is that each genotype carries two functions at
once, the old (ERE) and the new (SRE), which is what makes the pleiotropic
tradeoff between them measurable.
"""

import csv
import dataclasses
import gzip

from ridge import gb1

ANCESTRAL_RH = 'EGKA'
_STANDARD_AA = set('ACDEFGHIKLMNPQRSTVWY')


@dataclasses.dataclass
class SteroidData:
    """ The AncSR1 recognition-helix landscape on two response elements.

        `ere` and `sre` are the function (mean fluorescence) surfaces on the
        ancestral and derived DNA elements; `ere_active` and `sre_active` are the
        sets of helices called functional on each. The ancestral helix is active
        on ERE and absent from `sre_active`, so it lacks the new function.
    """
    ancestral_rh: str
    ere: gb1.Gb1Landscape
    sre: gb1.Gb1Landscape
    ere_active: frozenset
    sre_active: frozenset


def _open(path):
    """ :return: A text handle, transparently decompressing a .gz path """
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, encoding='utf-8')


def load_ancsr1(path, *, ancestral_rh=ANCESTRAL_RH):
    """ Loads the AncSR1 recognition-helix landscape.

        Every four-letter helix of standard amino acids carries a mean
        fluorescence and an active/null call on each of ERE and SRE. Rows with a
        non-standard residue are skipped.
    :param path: Path to the CSV (optionally gzipped)
    :param ancestral_rh: The ancestral helix, the start of every path
    :return: A SteroidData
    :raises ValueError: if the ancestral helix is not in the data
    """
    ere_values, sre_values = {}, {}
    ere_active, sre_active = set(), set()
    with _open(path) as handle:
        for row in csv.DictReader(handle):
            variant = row['variant']
            if any(char not in _STANDARD_AA for char in variant):
                continue
            ere_values[variant] = float(row['ERE_meanF'])
            sre_values[variant] = float(row['SRE_meanF'])
            if row['ERE_active'] == 'TRUE':
                ere_active.add(variant)
            if row['SRE_active'] == 'TRUE':
                sre_active.add(variant)
    if ancestral_rh not in ere_values:
        raise ValueError(f'ancestral helix {ancestral_rh!r} not found in {path}')
    return SteroidData(
        ancestral_rh=ancestral_rh,
        ere=gb1.Gb1Landscape(values=ere_values, wild_type=ancestral_rh),
        sre=gb1.Gb1Landscape(values=sre_values, wild_type=ancestral_rh),
        ere_active=frozenset(ere_active),
        sre_active=frozenset(sre_active),
    )
