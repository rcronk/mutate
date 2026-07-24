# K-axis: buildability as a function of coordination number

This package generalizes the protocell build/degrade question into a single
controlled experiment, and grounds it against mainstream population genetics
before making any claim.

## The one control variable

The protocell work established a distinction that matters: **tuning** an existing
function (a gradient exists, and evolution climbs it easily) is not the same as
**creating** a new coordinated structure (where nothing works until several
specific things are simultaneously right). The disagreement in the field is not
about tuning; it is about creation, and specifically about whether the fitness
landscape supplies a gradient of functional intermediates or not.

So we make that the knob. **K** is the coordination number: how many specific
things must be simultaneously right before *any* reward exists.

- **K = 1** is pure tuning. A gradient is present everywhere; structure is built
  easily.
- **K large** is irreducible: no functional intermediate, so selection is blind
  to progress and only mutation supply and neutral drift can cross the gap.
- **Selection strength** is a second dial. Turn it to zero and there is no
  differential reproduction at all, which is the **origin-of-replicator** limit,
  where "no gradient" is a logical necessity rather than a modeling choice.

The two questions the author cares about, de novo origin of coordinated function
and the origin of the replicator, are therefore two settings of one apparatus,
not two models.

## Honesty rules (bias guards, committed before results are trusted)

1. **No authored intermediate rewards.** Selection sees only whole-organism
   survival and reproduction. We never hand-pay a half-built structure to lead it
   toward the goal; injecting a gradient is injecting the conclusion. If we study
   how a gradient changes buildability, the gradient is an explicit, reported
   variable, never a hidden default.
2. **Neutral intermediates are the honest hard case**, and the default.
3. **Validate the engine against mainstream math before using it.** We do not get
   to claim "evolution cannot build this" on an engine no population geneticist
   would accept. Slice 5 does this validation first.
4. **Report buildability as a function of K and selection strength**, a curve,
   never a single universal verdict. Where real biology sits on the K-axis is a
   separate empirical question we do not prejudge.

## Slice 5 (this PR): the engine is trustworthy

A minimal Wright-Fisher engine (population.py) for a K-step structure with
neutral intermediates, checked against the analytic waiting time (analytic.py):

- **K = 1**: reproduces the exact geometric appearance time (ratio 0.997).
- **K = 2**: reproduces the Durrett-Schmidt drift-assisted law. Cutting the
  second mutation rate by 16 lengthens the wait by about sqrt(16) = 4, not by 16.
  The slope of log(wait) vs log(u2) is -0.56, the square-root law, not the naive
  -1. See data/waiting_validation.txt.

Because the engine matches the waiting time a population geneticist would compute,
it cannot be dismissed as rigged. That is the foundation the buildability(K)
slice stands on. Run it: `python -m kaxis.validate`.

## Slice 6: buildability(K), and what the gradient assumption is worth

With the engine trusted, slice 6 asks the real question. Building a K-part
structure is run in two regimes on the same engine and the same mutation supply:
no gradient (every intermediate neutral, nothing rewards a half-built structure)
and gradient (each completed step is itself beneficial). The selection dial is
first validated on its own: a beneficial mutant fixes at about Haldane's 2s
(`population.fixation_fraction` vs Kimura's formula in analytic.py).

Result (mean generations to build, N=1000, step rate 5e-4, selection 0.1):

| K | no gradient | gradient | cost ratio |
|---|-------------|----------|------------|
| 1 | 2.5         | 2.5      | 1.0x       |
| 2 | 101.8       | 39.4     | 2.6x       |
| 3 | 646.0       | 79.9     | 8.1x       |
| 4 | 2015.0      | 125.9    | 16.0x      |
| 5 | 3509.0      | 179.5    | 19.5x      |
| 6 | 4900.1      | 222.6    | 22.0x      |

With a gradient the cost grows about **linearly** in K; without one it grows far
faster, so the **cost ratio widens with every added part**. That widening is the
measured worth, in generations, of the gradient assumption. In a mutation-limited
regime (Nu << 1) the no-gradient case does not merely slow down, it stops
finishing within a fixed resource budget while the gradient still always builds
(see data/buildability_curve.txt). Run it: `python -m kaxis.buildability`.

This does not decide where real biology sits on the K-axis (how often a partial
structure is actually rewarded). It makes that the measurable question, which is
the honest and un-dismissable form of the argument.

## Next slices

- **Place real biology on the K-axis** using measured data: the ridge/ DMS
  landscapes for the low-K tuning end, de novo function frequencies such as Keefe
  and Szostak's 37-bit ATP binders for the "how rare is function at all" end.
- **A protocell demonstration** of the same K contrast in readable code, so a
  layperson can see the structure that did or did not get built, not only the
  curve.
- **Lit-check** (Avida, Tierra, and the waiting-time literature) before any
  write-up.
