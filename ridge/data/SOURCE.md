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
