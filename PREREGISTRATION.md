# Preregistration: Measuring the Rate at Which Mutation and Selection Generate Functional Information

**Status:** DRAFT. Not yet in force.
**Author:** Robert Cronk
**Finalized:** _(to be filled: date, git commit SHA, and public timestamp)_

---

## 0. What a preregistration is, and why this document exists

A preregistration is a public, timestamped statement of exactly what an experiment will
do and what result would prove the author wrong, written and published **before any
data is collected.**

The problem it solves is not dishonesty. It is that everyone, unavoidably, finds it
easier to see a result as confirming what they already believed. Given freedom to
choose the analysis after seeing the data, a researcher can nearly always find a
defensible path to their preferred conclusion without ever consciously cheating. Fixing
the analysis in advance removes that freedom.

The author of this project holds, and has stated publicly, a strong prior belief that
the answer will come out a particular way. That makes this document more necessary
here than in the average study, not less. **The value of any result this project
produces depends on this document being written first and adhered to afterward.**

Everything below is binding once finalized. Deviations are permitted but must be
recorded in Section 10 with a timestamp and a reason, and reported in any publication.

---

## 1. The question

When code is copied with random errors, and non-working copies are discarded, how much
*new functional information* accumulates, and how does that amount grow as more
computational resources are spent?

This is a question about a **rate**, and therefore about the shape of a curve. It is
deliberately not the question "can evolution produce complexity, yes or no," because
that question has no measurable answer.

---

## 2. Background: what is already established, and what is not

A literature audit was performed before finalizing this protocol. **Two novelty claims
made in an earlier draft of this document were found to be false and are withdrawn
below.** Recording that here rather than quietly deleting it is deliberate: a
preregistration that hides its own corrections is worthless.

### 2.1 Already established. Not claimed as novel here.

1. **Functional information has already been applied to digital organisms.** Hazen et
   al. (2007), who introduced the metric this study uses, applied it to Avida directly,
   measuring the distribution of function across randomly generated genomes and
   describing the resulting landscape as "islands of solutions."

2. **The information a fitness function contributes has been formalized and measured.**
   Dembski & Marks (2009, 2010) developed "active information" specifically to quantify
   how much problem-specific information a search is given, defined as how far the
   search outperforms blind search. Ewert, Dembski & Marks (2009) applied it to Avida,
   named the mechanism "stair step active information," and argued Avida's graded logic
   rewards supply it. **An earlier draft of this document asserted that nobody had
   quantified the scaffolding contribution. That assertion was false.**

3. **Complexity has been measured against population size in digital evolution.** LaBar
   & Adami (2016) swept population size from 10 to 10⁴ individuals over 2.5 × 10⁵
   generations with 100 replicates. **An earlier draft asserted that no scaling study
   existed. That assertion was too strong.** What that study did not do is measure
   functional information (it counted phenotypic traits) or fit a scaling law; it
   reported a non-monotonic pattern in which both small and large populations evolved
   greater complexity than intermediate ones.

4. **The claim that functional information increases under selection is live and
   contested, not settled.** Wong et al. (2023) proposed a "law of increasing functional
   information." Root-Bernstein (2024) published a critical response in PNAS, with a
   reply from the original authors in the same issue.

### 2.2 What remains open. This is where the project's contribution lies.

- **No fitted scaling law for functional information against total resources.** LaBar &
  Adami varied population size but measured trait counts and fitted no curve. Wong et
  al. assert that functional information increases without specifying a rate. The
  quantity `I_max(R)` has not been measured across orders of magnitude of
  organism-generations and fitted to competing functional forms.

- **Substrate tolerance has never been an independent variable.** Avida's instruction
  set and its mutational robustness are fixed design decisions. Ray (1991) explicitly
  designed the Tierran language because conventional machine languages were "too
  brittle to evolve," which concedes the point that substrate tolerance is decisive,
  but no study sweeps it and measures the consequence.

- **Active information has not been swept systematically.** It has been computed for
  particular Avida configurations, not varied as a controlled axis against substrate
  tolerance and resources simultaneously.

- **No published extrapolation** of a measured digital-evolution scaling law to
  biological resource scale with stated confidence intervals.

### 2.3 The methodological advantage

In biology, the fraction of sequences that are functional can only be estimated by
contested wet-lab proxies. Published estimates span roughly 1 in 10¹¹ (Keefe & Szostak
2001, from a random 80-mer library) to 1 in 10⁷⁷ (Axe 2004, for a 150-residue enzyme
fold), which is sixty-six orders of magnitude of disagreement driven by method and
target. **In a simulation this quantity can be computed exactly.** That is the central
methodological advantage of this approach and the reason for doing it in silico.

---

## 3. The measurement

The dependent variable throughout is **functional information**, after Hazen, Griffin,
Carothers & Szostak (*PNAS*, 2007):

```
I(Eₓ) = -log₂( F(Eₓ) )
```

where `F(Eₓ)` is the fraction of all possible genomes of a given length that achieve at
least degree `Eₓ` of the specified function. Units: bits.

`F` will be computed **exactly by exhaustive enumeration** at genome lengths where the
sequence space is small enough to enumerate, and by Monte Carlo sampling with reported
confidence intervals above that. The crossover point and the sampling procedure are
fixed in the protocol before runs begin.

The primary quantity reported is `I_max(R)`: the highest functional information
observed in any lineage, as a function of `R`, the total resources expended, measured
in organism-generations (population size × generations).

A secondary quantity is **coordination degree**: for any novel function that appears,
the number of mutations on its lineage that were not individually beneficial at the
time they occurred and are individually required for the function. Measured by lineage
replay and single-mutation knockout.

---

## 4. Hypotheses

Stated as competing models for `I_max(R)`, to be distinguished by fitting both to the
same data.

**H_log (the author's hypothesis).** Achievable functional information grows
logarithmically in resources:

```
I_max(R) = a · log(R) + b
```

Rationale: the number of sequences of length L grows exponentially with L, so the
fraction that are functional decays exponentially. If selection provides no substantial
advantage over undirected search, the attainable information grows only as the
logarithm of the resources spent. Under this model, doubling all the resources in the
experiment adds a small constant number of bits, and no achievable increase in
resources closes a large gap.

Informally: rolling more Scrabble dice for longer finds you four-letter words instead
of three-letter words. It does not find you a novel.

**H_pow (the mainstream-consistent alternative).** Cumulative selection substantially
outperforms undirected search, and achievable information grows as a power law:

```
I_max(R) = c · R^k    (k > 0)
```

Under this model, increasing resources continues to buy meaningful increments of
functional information, and extrapolation to biological scale is defensible.

These models make opposite predictions about what happens when the experiment is scaled
up, and they are distinguishable with modest compute.

---

## 5. Substrate

A virtual machine executing digital organisms in a single process. Design requirements,
fixed in advance:

- **No syntax errors.** Every possible instruction sequence is executable. A mutation
  changes what a program does, never whether it runs. (Rationale: Python source text
  makes most single-character mutations immediately lethal, which is a property of
  Python's grammar rather than a finding about evolution.)

- **Two-level translation.** Genome bits → codons → instructions, mirroring
  DNA → RNA → protein.

- **Tunable codon redundancy.** How many codons map to the same instruction is an
  experimental parameter, not a fixed assumption. This makes the substrate's tolerance
  for mutation an independent variable rather than a design decision to be argued over.

- **Full mutation operator set:** point substitution, insertion, deletion, segment
  duplication, inversion, and recombination. Duplication is included specifically
  because it is the mainstream proposed mechanism for the origin of new genes (Ohno
  1970); omitting it and then reporting that novelty does not arise would be circular.

Every run is seeded and exactly reproducible. Full phylogeny and all genomes are
retained for lineage analysis.

---

## 6. Experimental design

**Task.** Self-replication is required for persistence. Organisms that cannot
copy themselves leave no descendants. Layered on top is a formal-language production task
whose `F` is computable in closed form, providing a difficulty dial that tunes smoothly
across many orders of magnitude.

**Three swept axes:**

| Axis | Range | Purpose |
|---|---|---|
| Resources `R` | ≥ 6 orders of magnitude of organism-generations | The scaling law itself |
| Codon redundancy | none → 64:20 → overlapping frames | How much substrate tolerance matters |
| Fitness scaffolding | none → graded → full task rewards | How much information the experimenter supplies |

**Replicates:** n ≥ 30 independent seeded runs per cell of the design grid.

**Controls:**
- *Drift-only:* mutation with no selection. Baseline for how much functional
  information accumulates by chance alone. Any reported signal must exceed this.
- *Undirected search:* random genome sampling at matched resource cost. This is the
  comparison that decides H_log versus H_pow. Selection must beat it, and by how
  much is the entire result.

---

## 7. Calibration gate (mandatory, blocking)

Before any headline experiment is run, the simulator must reproduce a known published
positive result: the evolution of EQU under scaffolded rewards, at a rate statistically
consistent with Lenski et al. (2003).

**If this gate is not passed, no negative result from this project will be reported as
evidence about evolution.** A system that cannot produce complexity when complexity is
known to be producible has demonstrated a broken instrument, not a fact about nature.

This gate exists specifically to protect the project from its author's stated prior.
It is the single most important safeguard in this document.

---

## 8. Analysis plan (fixed in advance)

1. Fit both H_log and H_pow to `I_max(R)` by maximum likelihood.
2. Compare models by BIC. **Decision rule: ΔBIC > 10 constitutes decisive support.**
3. Report the fit for every cell of the design grid, not only the favorable ones.
4. Extrapolate the better-fitting model to `R = 10⁴⁰` organism-generations, an
   order-of-magnitude standing estimate for the total number of cells that have ever
   lived on Earth, and report predicted `I_max` with 95% confidence intervals.
5. Compare that prediction against reference scales for biological functional
   information, reported as a **range** rather than a single figure, since the
   underlying estimates are disputed: a single functional protein fold at
   F = 10⁻¹¹ (Keefe & Szostak) is ≈ 37 bits; at F = 10⁻⁷⁷ (Axe) it is ≈ 256 bits.

---

## 9. Falsification criteria

**The author's hypothesis (H_log) is falsified if:**

- H_pow is decisively favored (ΔBIC > 10) in a majority of design-grid cells under
  **unscaffolded** selection; **or**
- Extrapolation of the fitted curve to R = 10⁴⁰ predicts `I_max` exceeding 256 bits
  with the 95% confidence interval excluding H_log's prediction; **or**
- Any novel function with coordination degree ≥ 3 appears under unscaffolded selection,
  detected by held-out tests, in ≥ 5 of 30 replicates.

**The mainstream-consistent alternative (H_pow) is disfavored if:**

- H_log is decisively favored (ΔBIC > 10) under unscaffolded selection **and** the
  calibration gate was passed; **and**
- Extrapolation to R = 10⁴⁰ predicts `I_max` below the lower reference scale (37 bits)
  with 95% confidence.

Both criteria are symmetric in form and were written at the same time, before any data
existed.

---

## 10. Scope: what this project can and cannot establish

Written in advance so that the limits are on the record rather than negotiated after
the results are in.

**This project can establish:**
- A measured scaling law for functional information under mutation and selection in a
  defined substrate, with substrate tolerance swept as a parameter. Not previously
  published.
- A quantification, in bits, of how much functional information an experimental setup
  contributes through fitness scaffolding versus how much the evolutionary process
  generates. This makes a long-standing methodological criticism measurable.
- An exact value for `F` in a system where it is computable, against which the disputed
  biological estimates can be calibrated.
- A measured threshold for how much structure must exist in a state space before
  self-replication becomes findable within a given resource budget.

**This project cannot establish:**
- That biological evolution did not occur. A simulation is not chemistry, and any
  negative result is answerable with the objection that the substrate is
  unrepresentative. **This objection is valid, and it is the same objection this
  project levels at extrapolations from Avida. It applies symmetrically and will
  be stated as such in any publication.**
- That the origin of biological information required a mind. Functional information
  measures the rarity of working arrangements. It says nothing about meaning,
  reference, or intent, and no measurement in this project bears on those questions.
- Anything about evolutionary theory's other evidential bases: fossil succession,
  nested genetic hierarchies, biogeography, or directly observed speciation, none of
  which this experiment touches.

---

## 11. Amendments

Any deviation from this document after finalization is recorded here with date,
rationale, and git commit SHA. An amendment log with entries is normal and honest; an
empty log on a long project is itself suspicious.

| Date | Section | Change | Rationale |
|---|---|---|---|
| *(no amendments yet)* | | | |

---

## References

Citations below were checked against the primary source or its indexed record on
2026-07-19: titles, journals, volumes, page ranges, and the specific numerical claims
attributed to each. Two items carry an explicit caveat where verification was
incomplete. Anything not yet verified says so rather than appearing verified.

Axe, D. (2004). Estimating the prevalence of protein sequences adopting functional
enzyme folds. *J. Mol. Biol.* 341:1295-1315.

Dembski, W., Marks, R. (2009). Conservation of information in search: measuring the
cost of success. *IEEE Trans. Systems, Man and Cybernetics A* 39(5):1051-1061.
*(Caveat: pages and issue confirmed; the authors' own publication page lists the volume
as 5, which appears to be an error, since IEEE Trans. SMC-A was at volume 39 in 2009.
Confirm the volume against IEEE Xplore before citing in a manuscript.)*

Dembski, W., Marks, R. (2010). The search for a search: measuring the information cost
of higher level search. *J. Advanced Computational Intelligence and Intelligent
Informatics.* *(Caveat: existence and title confirmed; volume and page numbers not yet
verified. Do not cite with page numbers until checked.)*

Ewert, W., Dembski, W., Marks, R. (2009). Evolutionary synthesis of nand logic:
dissecting a digital organism. *Proc. IEEE Int. Conf. Systems, Man and Cybernetics*,
San Antonio TX, 3047-3053.

Hazen, R., Griffin, P., Carothers, J., Szostak, J. (2007). Functional information and
the emergence of biocomplexity. *PNAS* 104(suppl. 1):8574-8581.

Keefe, A., Szostak, J. (2001). Functional proteins from a random-sequence library.
*Nature* 410:715-718.

LaBar, T., Adami, C. (2016). Different evolutionary paths to complexity for small and
large populations of digital organisms. *PLoS Comput. Biol.* 12(12):e1005066.

Lenski, R., Ofria, C., Pennock, R., Adami, C. (2003). The evolutionary origin of
complex features. *Nature* 423(6936):139-144.

Ohno, S. (1970). *Evolution by Gene Duplication.* Springer.

Ray, T. (1991). An approach to the synthesis of life. In *Artificial Life II*, Santa Fe
Institute Studies in the Sciences of Complexity vol. X, Addison-Wesley, 371-408.

Root-Bernstein, M. (2024). Evolution is not driven by and toward increasing information
and complexity. *PNAS* 121(34):e2318689121.

Shen, X., Song, S., Li, C., Zhang, J. (2022). Synonymous mutations in representative
yeast genes are mostly strongly non-neutral. *Nature* 606(7915):725-731. (Contested:
Kruglyak et al. published "Insufficient evidence for non-neutrality of synonymous
mutations" in *Nature* 2023; the original authors responded in *Mol. Biol. Evol.*
41:msae224, 2024. The debate is unresolved and should be presented as such.)

Trifonov, E. (1989). The multiple codes of nucleotide sequences. *Bull. Math. Biol.*
51:417-432.

Wong, M., et al. (2023). On the roles of function and selection in evolving systems.
*PNAS* 120(43):e2310223120.
