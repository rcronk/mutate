# mutate

Measuring the rate at which mutation and selection generate functional information.

## What this project asks

When code is copied with random errors and non-working copies are discarded, how much
new *functional information* accumulates, and how does that amount grow as more
computational resources are spent?

This is a question about the shape of a curve, not a yes/no question about whether
evolution "works." The deliverable is a measured scaling law, extrapolated to biological
scale with stated confidence intervals, in a substrate whose tolerance for mutation is
swept as an experimental parameter rather than assumed.

## Start here

| Document | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The binding experimental protocol: hypotheses, measurements, and the specific results that would prove the author wrong. Written before any data is collected. |
| [`GLOSSARY.md`](GLOSSARY.md) | Every technical term in plain language, with worked examples. No background in biology or artificial life assumed. |
| [`legacy/`](legacy/) | The 2016-2017 first attempt, archived, **with published corrections**. Superseded; not evidence. |

## Status

Pre-implementation. The preregistration is in draft and is not yet in force.

## A note on bias

The author holds a strong prior view about how this will come out and has stated it
publicly. That is why this project is preregistered, why its falsification criteria were
written before any data existed, and why a mandatory calibration gate requires the
simulator to reproduce a known published positive result before any negative result from
it is reported. See [`PREREGISTRATION.md`](PREREGISTRATION.md) §0, §7, and §10.
