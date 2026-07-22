# Data sources

## weinreich2006_betalactamase_mic.csv

Minimum inhibitory concentration (MIC, ug/mL) of cefotaxime for all 32
combinations of five mutations in TEM-1 beta-lactamase, from:

  Weinreich DM, Delaney NF, DePristo MA, Hartl DL (2006).
  "Darwinian evolution can follow only very few mutational paths to fitter
  proteins." Science 312:111-114.

The five mutations are the promoter mutation g4205a and the amino-acid
substitutions A42G, E104K, M182T, G238S. Wild type (all zeros, "gAEMG") has
MIC 0.088; the full mutant (all ones, "aGKTS") has MIC 4100.

Obtained from the processed dataset at https://github.com/OgPlexus/DEFPreflect
(file "1. FINAL_DataBinary_MIC.csv"), which recomputes values from the original
paper. The published result to reproduce: of the 120 mutational trajectories
from wild type to full mutant, only 18 are selectively accessible (MIC
increases at every step).

## gb1_wu2016_landscape.csv

Binding fitness of all four-site combinatorial variants of the IgG-binding
domain of protein G (GB1) at positions V39, D40, G41, V54, from:

  Wu NC, Dai L, Olson CA, Lloyd-Smith JO, Sun R (2016).
  "Adaptation in protein fitness landscapes is facilitated by indirect paths."
  eLife 5:e16965.

Two columns: `variant`, a four-letter string of the amino acids at the four
sites (wild type is VDGV), and `fitness`, the enrichment-based binding fitness
normalised so wild type equals 1.0 (the paper's I20fit column, IgG selection).

Obtained from the authors' repository https://github.com/wchnicholas/ProteinGFourMutants
(file result/Mutfit, column I20fit). Restricted here to the 149361 variants that
use only the twenty standard amino acids and have a measured (non-NA) fitness,
out of the 20^4 = 160000 possible (93.4% coverage). Variants containing stop
codons or non-standard residues, and variants with no measurement, are dropped.

The empirical global maximum of this column is FWAA at fitness 8.76. The
landscape is rugged: it has 198 local maxima under single-substitution moves,
reproducing the paper's central finding that direct adaptive paths are often
blocked.
