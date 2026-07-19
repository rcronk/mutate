# How to register this preregistration

Two separate things, often confused. They are complementary, not alternatives.

| | OSF | PCI RR |
|---|---|---|
| What it is | A notary | A reviewer |
| Does anyone read it | No | Yes, real peer review of the design |
| Cost | Free | Free |
| Time | An afternoon | Months |
| Obligation | Disclose deviations | Follow the protocol, submit Stage 2 |
| What you get | Frozen timestamp and a DOI | Design critique plus a publication route |
| Blocks building | No | No |

**Do OSF first, this week. Submit to PCI RR in parallel. Keep building throughout.**

Neither one requires you to stop working. Building a simulator is not collecting data.
What you must not do after registering is run the definitive experiments and analyze them
before Stage 1 review concludes, if you are going the PCI route. Calibration and pilot
work are expected and fine.

---

## Part 1: OSF (do this first)

OSF timestamps and freezes the document so nobody, including you, can later claim it said
something different. It is a notary. No one reviews it, no one approves it, and there is
no waiting.

1. Create an account at [osf.io](https://osf.io). Link your ORCID if you have one; if
   not, get one free at [orcid.org](https://orcid.org) first. It is the standard
   researcher identifier and takes five minutes.
2. Create a new **Project**. Name: `mutate: measuring the rate at which mutation and
   selection generate functional information`.
3. Under the project, create a **Registration**. Choose the **OSF Preregistration**
   template, or **Open-Ended Registration** if you would rather submit this document
   as-is without mapping it to their fields.
4. Fill the fields from `PREREGISTRATION.md` (mapping below).
5. Attach `PREREGISTRATION.md`, `GLOSSARY.md`, and a link to the GitHub repo at the
   specific commit SHA.
6. Submit. Registration is **permanent and public**. There is an optional embargo of up
   to four years if you want it private until publication; for this project, public
   immediately is the stronger choice, since the whole point is showing the commitment
   preceded the data.

### Field mapping

| OSF field | Source |
|---|---|
| Title | Line 1 of `PREREGISTRATION.md` |
| Description | §1, The question |
| Hypotheses | §4, both H_log and H_pow verbatim |
| Design plan | §5 and §6 |
| Sampling plan | §6, replicates (n ≥ 30 per grid cell) |
| Variables | §3, functional information and coordination degree |
| Analysis plan | §8, all five steps |
| Inference criteria | §9, all of it |
| Existing data | "No data collected." Say this explicitly. |
| Other | §7 calibration gate, §10 scope, §2 prior-art audit |

Two fields matter more than the rest. **Existing data** must say no data has been
collected, because that is the claim the registration exists to make. And **inference
criteria** must contain §9 in full, because that is the part that makes the result mean
something.

---

## Part 2: PCI RR (submit in parallel)

[rr.peercommunityin.org](https://rr.peercommunityin.org). Free, non-commercial, no
article charges.

You submit a **Stage 1** manuscript: research question, hypotheses, methods, analysis
plan, and any pilot data. Reviewers critique the design only, since there are no results
yet. If recommended, you have in-principle acceptance: a list of PCI RR-friendly journals
have committed to accepting the recommendation without further peer review, and Peer
Community Journal will publish it directly, free for both authors and readers.

The commitment runs both ways. They commit to publishing regardless of how the results
come out. You commit to running the protocol as approved and reporting what happens.

**What this is worth here specifically:** the most likely outcome of this project is a
result showing that something did not happen. Null results are hard to publish through
normal review. In-principle acceptance removes that risk entirely, which for this project
is worth more than it would be for most.

**Expect the review to be rough.** The likely line of attack is whether a designed
substrate can support extrapolation to biology. That is the hardest question in the
project and the same objection this project levels at Avida. Section 5's DFE calibration
is the answer, and Stage 1 is the right place to find out whether it holds up, before a
year of work rather than after.

---

## What I cannot do

I cannot submit either of these for you, and would not even with browser access.

A registration is a non-repudiable public commitment made in your name, tied to your
identity, affirming that the work is yours and that no data has been collected. Its
entire value comes from you being the one who made it. Someone else filing it defeats the
instrument.

The mapping above should make it a short mechanical task.

---

## Order of operations

1. Get an ORCID if you do not have one.
2. Register on OSF. Public, no embargo.
3. Record the OSF DOI and date in `PREREGISTRATION.md` under **Finalized**, and change
   the status line from DRAFT.
4. Start building. Interpreter first.
5. Format Stage 1 for PCI RR and submit whenever ready. No rush; building continues.
