# Protocell: plan and honesty rules

A more faithful evolution simulation than the `sim/` model, whose fatal flaw was
that one character mutation changed one number that stood for an entire
biological system (a 1:1 mutation-to-system ratio). Here a creature is a **pool
of functions** ("proteins"), each doing real multi-step work, called
stochastically to run a little cell. Mutation acts on the functions, so a single
mutation is a small change to a multi-part system, closer to a point mutation in
a gene.

This file is committed **before** the simulation is trusted, as a guard against
moving the goalposts. If a result later contradicts a claim here, the claim
loses.

## The one question everything serves

**Under mutation and selection, does the functional (specified) information in a
cell's protein pool go UP or DOWN, and how does that depend on the knobs we had
to choose?**

This is a *direction*, not a verdict. It can register increase (building) or
decrease (degradation / genetic entropy) as a real result. No simulation can
honestly deliver a universal "evolution can/can't build complexity"; any such
claim just reflects substrate choices. We report the direction and its
dependence on the knobs.

Specified information here means the amount of the pool that is **constrained by
function**: positions where a mutation reduces fitness. Random text has high
Shannon entropy but low specified information; we measure the latter, by mutation
sensitivity. This is the same functional-information idea used on real proteins
in the `ridge/` work.

## The model

- **Protein**: a Python function, given as source, that reads and writes cell
  state and the environment. A mutation that stops it running is a *misfolded*
  protein: nonfunctional, cleared by turnover. (Measured earlier: raw
  function-source mutation tolerates ~10% of single mutations, inside biology's
  6-34%, so this is a defensible robustness level without a genetic-code layer.)
- **Cell**: a pool of proteins plus energy and internal registers. Each tick,
  proteins execute in random order and their combined effect keeps the cell
  alive (metabolism) or divides it (reproduction). Proteins have lifespans;
  old ones are cleared.
- **World**: a finite, regrowing food pool the cells compete for. Selection is
  emergent, survive and divide, nothing hand-picked.
- **Mutation** (on division): the empirically **observed** spectrum, point
  substitutions, small insertions/deletions, and whole-protein duplication and
  deletion, at roughly observed relative rates. Observed, not inferred from
  phylogeny.

## Two seeds, to measure both directions

- **Minimal seed**: a pool too poor to sustain the cell. Does mutation +
  selection build it up (functional information rises)?
- **Working seed**: a hand-written pool that lives and divides. Does it hold, or
  degrade (functional information falls)?

## Honesty rules (bias guards)

1. **Generic primitives only.** Proteins are built from generic operations
   (arithmetic, logic, read/write state, eat, divide). No task-specific freebie
   like a `provision_offspring` primitive.
2. **No fine-grained chooser.** Proteins are called stochastically. We never add
   a "use whichever protein/copy works best" dispatcher; that would be us doing
   selection. Selection happens only at the level of which cells survive and
   divide.
3. **Calibrate what we can to measured numbers.** Mutation tolerance to the
   ~6-34% from real proteins; mutation spectrum to observed rates.
4. **State every contrivance.** The cell inherits its core execution machinery
   (there is no from-scratch ribosome); we evolve the workload proteins. Said in
   the open.
5. **Report direction and dependence, not a verdict.**
6. **Readable, not just measurable.** Every run can dump its proteins as source,
   so a layperson can *see* what changed, not only trust a number.

## Vertical slices (thin, each tests an assumption)

- **Slice 1 (this PR): can a stochastically-called protein pool run a living,
  dividing cell at all?** Hand-written working pool vs a minimal one. No mutation
  yet. Feedback: does the pool-of-functions substrate host life, and what must a
  protein be able to do? Validates the substrate before evolution.
- **Slice 2**: mutation on division (the observed spectrum); run a population;
  the two seeds. Feedback: does minimal ever bootstrap; does working degrade.
- **Slice 3**: the metrics, functional/specified information direction, pool
  complexity, per-generation source dump.
- **Slice 4+**: protein complexes (proteins combining into machinery), and the
  knob-dependence study; then lit-check for prior art before any write-up.

## Prior-art / publishability

Digital evolution is a crowded field (Avida, Tierra, and their critiques). We do
NOT assume this is novel. Before any write-up we lit-check specifically for: the
functional-information-direction readout on a protein-pool cell with an observed
mutation spectrum. If it is prior art, the value is a clean teaching artifact,
not a paper. We decide that on evidence, later.

## Slice findings (a running log, so the record shows what we learned)

- **Slice 1**: a stochastically-called protein pool hosts a living, dividing,
  competing population; a pool that cannot feed dies. Substrate validated.
- **Slice 2** (mutation, observed spectrum): three things surfaced.
  1. The working pool tolerates observed-spectrum mutation and persists (no
     meltdown at point rates 0.5-2.0 per division).
  2. A non-reproducing seed cannot evolve at all: no feeding, no division, and
     mutation only happens at division, so no variation is ever generated. The
     build-test seed must reproduce. Added `crude_pool` for that.
  3. The crude reproducing pool does NOT build better function: at a food-capped
     carrying capacity a more efficient mutant does not out-reproduce, so there
     is no selection gradient rewarding function. What accumulates is
     duplication and degradation, not improvement. **Slice 3 needs an
     environment that rewards function (a selection gradient), plus the
     specified-information metric, before build-vs-degrade can be measured.**

## Revisable assumptions (expect slice feedback to change these)

The protein/cell API, the primitive set, energy/cost/threshold parameters, and
the mutation rates are all first guesses, to be adjusted as the slices tell us
what the substrate actually needs.
