# mutate

Experiments in what happens to source code when you copy it with random errors and throw
away the copies that stop working.

## What this actually shows

Not what it was originally claimed to show. The honest finding is about **software**, not
biology: which parts of a codebase survive random change is determined by what the tests
cover and by how tightly the syntax couples things together. Paired tokens survive because
breaking one unbalances the other. Covered branches survive because breaking them fails a
test. Everything else rots.

That is a real and reproducible result, and it has a practical use: it is
**mutation testing**, the established technique of deliberately corrupting code to find
out what your test suite actually protects. The short-circuit finding in the body-plans
experiment, where unreached `elif` branches decayed while covered ones stayed pristine, is
exactly the kind of blind spot coverage percentages hide.

## Tracks

**Legacy track (active).** The original experiments, made runnable, seeded, and
reproducible, with every overblown claim corrected. Plus a self-replicating creature that
eats, ages, reproduces, and dies, and eventually a 2D world it has to survive in.

**Scaling study (on hold).** [`PREREGISTRATION.md`](PREREGISTRATION.md) is a design for a
much larger study, retained as a record of the discussion. It is not in force, is not
registered, and contains a known fatal defect documented at the top of the file.

## Start here

| Document | What it is |
|---|---|
| [`legacy/`](legacy/) | The original experiments and their corrections. |
| [`GLOSSARY.md`](GLOSSARY.md) | Technical terms in plain language, with worked examples. |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | On-hold design for a larger study. Read the status block first. |

## Honesty note

These experiments do not demonstrate anything about biological evolution, and earlier
versions of this repository claimed they did. Those claims are corrected in
[`legacy/README.md`](legacy/README.md) section A, published unprompted before any external
critique. The corrections materially weaken the original conclusions.
