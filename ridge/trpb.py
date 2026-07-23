""" trpb.py - loads the tryptophan synthase (TrpB) four-site landscape.

TrpB is a third real optimisation landscape, after beta-lactamase and GB1, and
it adds a function type the others do not have: enzyme catalysis measured by
growth. More active variants of the enzyme let a tryptophan-starved E. coli grow
faster, so fitness here is a relative growth rate, not a binding or resistance
readout.

The four varied sites (183, 184, 227, 228) in the enzyme's active site form the
same four-amino-acid genotype as GB1, so this loads straight into a Gb1Landscape
and runs through the shared four_site analysis unchanged. The wild-type parent
enzyme has VFVS at these sites.
"""

from ridge import gb1

WILD_TYPE = 'VFVS'


def load_trpb_landscape(path, *, wild_type=WILD_TYPE):
    """ Loads the TrpB four-site landscape into a Gb1Landscape.
    :param path: Path to the CSV with `variant` and `fitness` columns
    :param wild_type: The parent enzyme's residues at the four sites
    :return: A Gb1Landscape whose wild type is the TrpB parent
    """
    land = gb1.load_gb1_landscape(path)
    land.wild_type = wild_type
    return land
