# Glossary

Plain-language definitions for every term used in this project's design. Written so
that someone with no background in evolutionary biology or artificial life can read
the experimental protocol and know exactly what is being claimed and measured.

Where the mainstream position and this project's hypothesis differ, both are stated.

---

## Core concepts

**Substrate**
The medium the digital organisms are made of. Python source text is one substrate.
A custom instruction set is another. DNA is biology's substrate. The choice matters
enormously, because it determines how a random change translates into a change in
behavior.

**Genotype**
The organism's code — the actual sequence of characters, bits, or instructions that
gets copied and mutated.

**Phenotype**
What the organism *does* when that code runs. Its behavior.

**Genotype–phenotype map**
The rule connecting the two: how a change in the code produces a change in behavior.
This is the single most important design decision in the whole project. In Python
source, most single-character changes produce a syntax error — the organism doesn't
run at all. In DNA, many single-base changes produce no behavioral change whatsoever.
These are wildly different maps, and they produce wildly different results from the
same evolutionary process.

---

## Kinds of mutation

**Point mutation**
Change one symbol to another. `9` becomes `3`.

**Insertion / deletion (indel)**
Add or remove symbols. The current `mutate.py` can insert but *cannot delete* —
genomes can only grow.

**Duplication**
Copy a stretch of code so it appears twice. Biology's mainstream explanation for
where new genes come from (Ohno, 1970): once there are two copies, one can keep doing
the original job while the other is free to change without penalty. **The current
`mutate.py` cannot do this at all.** Any conclusion about novel function drawn from a
system lacking duplication is open to the objection that the mechanism under test was
never implemented.

**Inversion / translocation**
Reverse a stretch of code, or move it elsewhere.

**Recombination (crossover / "sex")**
Combine parts of two different organisms' genomes into one offspring. Lets beneficial
changes that arose in separate lineages be brought together. Without it, all
beneficial changes must arise sequentially in a single line of descent.

---

## Selection

**Fitness**
A number saying how well an organism does. Higher fitness means more offspring.

**Fitness function**
The rule that assigns that number.

**Binary fitness**
Pass or fail, alive or dead. Nothing in between. *This is what every experiment in
the original `mutate.py` used* — the test suite either exits 0 or it doesn't.

**Graded fitness**
A continuous score. Allows "slightly better," which is what makes gradual improvement
possible at all.

**Fitness landscape**
Picture every possible genome laid out on a map, with height representing fitness.
Evolution is a walk across this landscape. A *gradient* is a slope to climb. Binary
fitness produces a landscape with no slopes — just a flat plateau with lethal cliffs.
Nothing can climb anything, because there is no "uphill."

**Purifying (negative) selection**
Selection that removes harmful changes. It *conserves* what already works. This is
the only kind of selection present in the original experiments.

**Positive selection**
Selection that favors improvements, driving change toward something new. Requires a
gradient, and therefore requires graded fitness. **No experiment in this repository
has yet used positive selection.**

**Genetic drift**
Change in a population that happens by chance rather than by selection, when
variations make no fitness difference. Real, and a major force in small populations.

> **Worked example — the beak result.** `test_beak.py` asserts the beak length is
> ≤ 9. The ancestor returns 9, which already passes. So do 8, 5, and 3 — every value
> passes equally, and none is favored. The observed drift from 9 to 3 was therefore
> *genetic drift under a ceiling constraint*, not adaptation. The original wiki
> presents this as the project's one demonstration of adaptation. It is not one.

**Scaffolding**
Rewarding intermediate steps toward a goal, rather than only the goal. Lenski et al.
(2003) rewarded simple logic functions and observed a complex one (EQU) appear.
Mainstream reading: selection built complexity from simpler parts. This project's
hypothesis: the reward schedule itself supplied the information, and the scaffold is
smuggled guidance. **This project's plan is to measure how much information the
scaffold contributes, rather than argue about it.**

**Held-out test**
A capability the fitness function never rewards, checked separately. If organisms
acquire it anyway, that is genuine novelty rather than teaching to the test. This is
the project's main defense against fooling itself.

---

## The central measurement

**Functional information**
The project's core metric, from Hazen, Griffin, Carothers & Szostak (*PNAS*, 2007):

```
I = -log2(F)
```

where `F` is the fraction of *all possible* sequences of a given length that perform
the function at least as well as the one in hand. Measured in bits.

The point: it measures **how rare the working arrangements are**, not how improbable
one particular arrangement is. That distinction is the whole argument.

> **Worked example.** Genomes are 100 bits long, so there are 2^100 possible genomes.
> Suppose 2^60 of them can self-replicate. Then F = 2^60 / 2^100 = 2^-40, and the
> functional information of self-replication in this substrate is **40 bits**.

> **Why this answers the "any outcome is improbable in hindsight" objection.**
> That objection says: any specific arrangement of sand grains is astronomically
> improbable, so pointing at one and calling it special is hindsight. But functional
> information is not about a specific arrangement. It is about the *size of the class*
> of arrangements that work. Almost all sand arrangements are noise; a vanishingly
> small fraction are grammatical English describing true facts. That fraction is `F`,
> and it is small **independent of any observer**. Function is defined by whether the
> thing works, not by whether someone finds it meaningful. This makes the rarity
> claim measurable rather than rhetorical.

> **What functional information deliberately does not capture.** It says nothing
> about *meaning* or *reference* — whether symbols point to things in the world, and
> whether that requires a mind. That is a philosophical claim, not a measurable one.
> This project can measure rarity of function. It cannot measure whether meaning
> requires a mind. Keeping these separate is what allows the results to be taken
> seriously; blending them is what gets work in this area dismissed unread.

**Coordination degree**
For a newly appeared function: how many mutations were required that were *not
individually beneficial at the time they occurred*. Measured by tracing the lineage
backward and, for each mutation, replaying its ancestral context to see whether it
helped, hurt, or did nothing when it arose; then reverting each one to check whether
the function still works without it.

This is the number that decides the project's central question. The hypothesis here
predicts it is essentially always 0 or 1. Lenski et al. reported paths to EQU that
included mutations which were harmful when they arose, implying a higher number.

---

## Architecture

**Virtual machine (VM)**
A small simulated computer, written in Python, that runs organism genomes as
programs. Runs entirely inside one process — no forking, no operating system
processes. Millions of organisms instead of thousands.

**Instruction set**
The list of operations an organism's code can express. Designed so that *every*
possible sequence is runnable — there is no such thing as a syntax error. A mutation
changes what a program does, never whether it parses.

**Two-level translation**
Genome bits → codons → instructions. Mirrors DNA → RNA → protein: the organism's
stored information is not directly its machinery, but is *translated* into machinery
through an intermediate code.

**Codon table**
The lookup table performing that translation. In biology, 64 codons map to about 20
amino acids, so several codons mean the same thing.

**Redundancy (degeneracy)**
How many codons map to the same instruction. High redundancy means many mutations
change nothing — the organism is buffered against damage.

**Neutral mutation**
A mutation with no effect on behavior or fitness.

**Neutral network**
The set of genomes that all produce the same behavior, connected by neutral
mutations. A population can wander across this network without penalty, accumulating
changes that do nothing on their own but may enable something later. Large neutral
networks make evolution easier; small ones make it nearly impossible.

**Redundancy dial**
This project's key innovation: **making codon-table redundancy an adjustable
parameter rather than a fixed assumption.** Set it to zero and the substrate is as
brittle as Python source. Set it to 64→20 and it is as buffered as textbook DNA.
Overlay a second reading frame and the redundancy gets consumed by the second code,
collapsing the effective neutral space — the scenario implied by Trifonov's work on
multiple overlapping codes in DNA.

Every position in the dispute over how forgiving biology "really is" becomes a
setting on this dial. The disagreement becomes an independent variable instead of an
argument.

**Overlapping reading frames**
The same sequence read starting at different offsets, encoding different things
simultaneously. Real: bacteriophage φX174 has genuinely overlapping genes.
Double-stranded DNA has **six** reading frames (three per strand, two strands).

---

## Experimental method

**Replicate**
One complete run. Because evolution is random, a single run proves nothing. Multiple
independent runs are needed to say anything about what typically happens.

**Seed**
The number initializing the random number generator. Recording it makes a run exactly
reproducible.

**Organism-generations**
Population size × number of generations. The project's measure of total evolutionary
resources expended — the "how much evolution happened" number.

**Calibration gate**
A mandatory check, before any headline experiment, that the simulator can reproduce a
known published positive result (Lenski's EQU under scaffolding). **Its purpose is to
protect this project from itself.** If the rig cannot produce complexity even when
complexity is known to be producible, then finding no complexity later means the
equipment is broken, not that evolution failed. Passing the gate is what makes a
later negative result mean something.

**Null result**
Finding nothing. Only informative if the experiment was capable of finding something —
hence the calibration gate.

**Preregistration**
Writing down, publicly and with a timestamp, exactly what result would prove the
hypothesis wrong — *before* running anything. Prevents unconscious reinterpretation
of whatever happens. Given that the author of this project holds a strong prior view
and has said so openly, this is the single most credibility-preserving step available.

**Scaling law**
How a measured quantity grows as resources grow. Here: how much functional
information accumulates as organism-generations increase. The project's central
claim is a claim about this curve's shape.

**Extrapolation with confidence intervals**
Fitting the measured curve, extending it to biological scale, and stating the
uncertainty honestly. If achievable functional information saturates (flattens out),
more time and bigger populations do not help, and biological complexity stays out of
reach. If it keeps climbing as a power law, it may not.

---

## Prior work referenced

**Avida**
A widely used artificial life platform with a syntax-error-free instruction set.

**EQU**
A two-input logic function requiring at least five coordinated operations. The target
in Lenski et al. (2003).

**Lenski, Ofria, Pennock & Adami (2003)**, *Nature* 423:139
Evolved EQU from replication-only ancestors in 23 of 50 populations **when simpler
logic functions were also rewarded**, and in **0 of 50** when only EQU was rewarded.
The strongest existing empirical claim against this project's hypothesis, and also —
via its own control condition — the strongest evidence that scaffolding is doing
substantial work.

**Tierra (Ray, 1991)**
Digital organisms competing for CPU time, in which parasites and hyperparasites
appeared that were never designed in. A data point for novelty arising under a
replication-only fitness function.

**Ohno (1970)**
Proposed gene duplication followed by divergence as the origin of new genes.

**Trifonov (1989)**
Catalogued multiple overlapping codes sharing the same DNA sequence.

**dN/dS**
A standard method comparing rates of amino-acid-changing to silent substitutions,
using silent sites as a neutral baseline. Relevant because it works, which means
neutral variation in real genomes is not zero — placing a floor under how brittle
biology can be argued to be.
