# Legacy: Initial Findings (2016-2017)

> **Status: the original claims are corrected; the experiments now run.**
>
> This directory holds the first version of the `mutate` project and its published
> writeup, originally hosted on the GitHub wiki.
>
> **Section A corrects the original claims.** These were published by the author,
> unprompted, before any external critique, and several of them materially weaken
> conclusions stated in the original text. Section C reproduces that original text
> unchanged.
>
> **Section B reports what actually happens when the experiments are rerun today**,
> across five seeds at 1000 generations each, reproducible from a seed and a command.
> Where the fresh runs bear on a correction, Section A links to them.
>
> **What these experiments show is about software, not biology.** Which parts of a
> codebase survive random change is determined by what the tests cover and by how
> tightly the syntax couples things together. The original writeup drew conclusions
> about evolution that the experiments do not support. See A7.

---

## Section A. Corrections to the original findings

These are errors and overstatements identified on review in 2026. Each is stated plainly
and located in the original text.

### A1. The beak result is genetic drift, not adaptation

The original text (Section "Beak Length - tested") concludes: *"Adaptation works."*

It does not demonstrate adaptation. `test_beak.py` asserts:

```python
self.assertGreaterEqual(9, mutated_beak.get_beak_length())
```

This passes whenever the beak length is **≤ 9**. The ancestor returns 9, which already
passes. So do 8, 5, and 3. Every value passes *equally*, and none is favored over
any other. There is no selective advantage to a shorter beak anywhere in this experiment.

The observed change from 9 to 3 is therefore a **random walk under a ceiling
constraint** (genetic drift), not selection for a shorter beak. To have tested
adaptation, the experiment would have needed a fitness measure that scores shorter
beaks *better* rather than merely *acceptable*.

This matters because the beak experiment was the project's only claimed demonstration of
constructive change. That claim is withdrawn.

**The committed artifact does not reproduce the claimed result.**
`artifacts-2016/mutated_beak.py` is byte-identical to `beak.py` and returns 9, not 3.
The diff is empty. The 9 to 3 outcome described in the writeup is not recoverable from
anything in this repository.

**Rerunning it settles the question.** Across five seeds at 1000 generations each, the
`9` was never changed to any other digit, not once. Every accepted mutation was
whitespace or a layout change:

```
-def get_beak_length():
-    return 9
+def get_beak_length():  return   9
```

Two things follow. There is no selective pressure toward a shorter beak, because the
test accepts every value at or below 9 equally. And a single digit inside a 35 byte
file is such a small target that random mutation rarely lands on it at all, so even
neutral drift to a different digit is uncommon. The claim "Adaptation works" is
withdrawn, and the withdrawal is now backed by a rerunnable experiment rather than by
reading the test.

Reproduce with: `python legacy/run.py beak --seed 1 --generations 1000`

### A2. No experiment here used positive selection

Every selector in this version is **binary**: the test suite either exits 0 or it
does not. A binary viability filter implements *purifying selection* only: it removes what
breaks and conserves what works. It cannot implement positive selection, because there
is no such thing as "slightly better" in a pass/fail test, and therefore no fitness
gradient for anything to climb.

Given that, the observed outcome (protected regions conserved, unprotected regions
degraded, nothing new appearing) is the mathematically expected behavior of the setup.
It confirms that purifying selection conserves information, which is uncontested
textbook biology.

**The original conclusion generalizes beyond what was tested.** The claim that mutation
and selection lack creative power was not tested here, because a mechanism capable of
producing directional change was never present in any run.

### A3. The mutation operator omits deletion and duplication

`Creature._flawed_copy` implements four operators: prepend, append, insert, and
overwrite. It therefore **cannot delete**, and genomes can only grow, which is the
direct cause of the "garbage numbers at the top and bottom of the file" observed in
nearly every experiment. That artifact is a property of the operator set, not a finding.

More significantly, it **cannot duplicate**. Gene and segment duplication followed by
divergence (Ohno, 1970) is the mainstream proposed mechanism for the origin of new
genes: a redundant copy is released from purifying selection and free to change while
the original continues functioning. Reporting that no new functions arose, in a system
that cannot perform the operation proposed to produce new functions, is circular.

*In fairness to the original:* both operators are listed as planned work in the
"Next steps" section (item 3) of the original text. The criticism is of the conclusions
drawn before they were implemented, not of the author's awareness of the gap.

**Correction to this correction.** Both operators are now implemented, and adding
deletion does **not** stop the junk from accumulating. An earlier version of this
section implied it would. It does not, for two reasons found by measurement:

- Deletion and duplication cancel each other out on average, since both draw span
  lengths from the same distribution.
- Growth is actually driven by the three insert-type operators, each of which splices
  in a mutation string averaging about 2.6 characters, because the Python keywords in
  the mutation alphabet are around six characters long. `overwrite` is not
  length-preserving either: it replaces one character with a possibly six-character
  keyword.

Deletion dilutes growth by consuming part of the operator budget, but does not reverse
it. Section B reports the measured difference between the two operator sets.

### A4. The abiogenesis experiment had no binding filter

`abiogenesis.py` is an empty file. The selector runs it and checks for a zero exit code.
An empty Python file exits 0. So does almost any file consisting of stray numeric
literals. **The filter never rejected anything on functional grounds**, so the run was an
unconstrained random walk, and `artifacts-2016/mutated_abiogenesis.py` is what an unconstrained random
walk produces.

The original text reasons correctly that there is no natural selection before
replication. That much is mainstream and is not disputed. But "no natural selection" is
not the same as "uniform random sampling": origin-of-life proposals rest on a
non-uniform state space: bond energies, thermodynamic funnels, autocatalysis,
template-directed ligation, concentration mechanisms. This experiment models a flat,
uniform space in which every symbol is equally probable and equally stable.

The experiment therefore does not test the abiogenesis claim; it tests a different claim
that no one holds. It should not be cited as evidence about the origin of life.

### A5. The published evidence is currently unviewable

All eight images in the original wiki page were hosted on temporary OneDrive URLs
(`*.files.1drv.com`). **As of 2026-07-19, every one returns 404 or 503.** The wiki has
been presenting its conclusions with no accessible evidence for an unknown period.

The diffs have been regenerated as text from the source files preserved here and are
available in [`diffs/`](artifacts-2016/diffs/). They are reproducible from this repository, which the
images were not. This is why evidence now lives in version control rather than in
external image hosting.

### A6. Two experiments can never be reproduced as originally run

`hello_world_tested` and `english` use pylint as a **selector**, not as tooling. What
survives in those runs is whatever pylint of that era happened to accept, so the pylint
version is part of the experimental setup.

The original runs did not record which pylint they used, and pylint has changed
substantially since 2016. It now enforces rules that did not exist then, including
f-string preferences, explicit file encodings, and exception specificity. A mutation
that survived selection in 2016 may be rejected today purely because the selector
became stricter.

The 2016 numbers for those two experiments are therefore **permanently
unreproducible**. Fresh runs reported in Section B are new measurements under a
recorded pylint version, not confirmations of the old ones, and they should not be read
as agreeing or disagreeing with the original figures. Every run now records
`pylint_version` in its manifest so this cannot recur.

### A7. Scope of the original conclusion

The concluding claim, that mutation and selection "were not shown to have creative
power," is accurate as literally stated but was read, including by the author, as
support for a much broader claim about biological evolution. The experiments here
involve a single organism at a time, a brittle substrate in which most mutations are
immediately fatal, no population, no drift, no recombination, and no fitness gradient.
No conclusion about biological evolution follows from them.

---

## Section B. What happens when the experiments are rerun (2026)

Every number below comes from `legacy/summarize.py` reading run manifests. Nothing is
typed by hand. Reproduce the whole table with:

```
python legacy/run.py --all --seed 1 --generations 1000
python legacy/summarize.py --markdown
```

Five seeds per condition, 1000 generations each, 60 runs total. "2016 set" is the
original four operators, which can only grow a genome. "all six" adds deletion and
duplication.

| experiment | operators | selector | seeds | accepted / 1000 | range | bytes |
|---|---|---|---|---|---|---|
| abiogenesis | 2016 set | execution only | 5 | 175 (17.5%) | 99-290 | 0 to 146 |
| abiogenesis | all six | execution only | 5 | 404 (40.4%) | 340-517 | 0 to 101 |
| beak | 2016 set | test_beak.py | 5 | 43 (4.3%) | 10-66 | 35 to 80 (2.3x) |
| beak | all six | test_beak.py | 5 | 49 (4.9%) | 29-69 | 35 to 44 (1.2x) |
| body_plans | 2016 set | test_body_plans.py | 5 | 203 (20.3%) | 181-235 | 1169 to 1416 (1.2x) |
| body_plans | all six | test_body_plans.py | 5 | 273 (27.3%) | 257-305 | 1169 to 1275 (1.1x) |
| english | all six | test_english.py | 5 | 292 (29.2%) | 253-388 | 118 to 238 (2.0x) |
| hello_world_tested | all six | test_hello_world_tested.py | 5 | 472 (47.2%) | 397-535 | 149 to 521 (3.5x) |
| hello_world_untested | 2016 set | execution only | 5 | 469 (46.9%) | 456-509 | 45 to 938 (20.8x) |
| hello_world_untested | all six | execution only | 5 | 580 (58.0%) | 553-619 | 45 to 640 (14.2x) |
| multiple_functions | 2016 set | test_multiple_functions.py | 5 | 35 (3.5%) | 24-52 | 403 to 437 (1.1x) |
| multiple_functions | all six | test_multiple_functions.py | 5 | 39 (3.9%) | 27-51 | 403 to 420 (1.0x) |

`english` and `hello_world_tested` have no 2016-set rows: those two use pylint as a
selector and are reported under the recorded pylint version only, for the reason given
in A6.

### D1. What survives is exactly what something checks

Acceptance rate falls as protection rises, and the ordering is clean:

| experiment | accepted | what protects it |
|---|---|---|
| multiple_functions | 3.9% | four functions, each tested, plus an aggregate test |
| beak | 4.9% | one tested return value in a 35 byte file |
| body_plans | 27.3% | one of nine branches is reached and tested |
| english | 29.2% | spell check plus pylint |
| abiogenesis | 40.4% | nothing; an empty file already exits 0 |
| hello_world_untested | 58.0% | nothing but syntax |

This is the honest result of the whole project, and it is about software. A mutation
survives when nothing observes the thing it broke. That is the same statement as
"surviving mutants indicate weak tests," which is the premise of mutation testing.

### D2. Short-circuit evaluation produces three tiers, not two

The original writeup noticed that branches after the taken one decayed. The rerun shows
a sharper three-way split. From `results/body_plans/seed-1/end.py`:

```python
        if self.body_plan == 1:            odf.dengscYriptioYR= self.k8ingddomp+ ...
        elif self.body_plan == 2:
            Beff.deT =sZn =eslf.k in idom + '%-=' + 'soi =d wi   xth  495plag 2 ...'
        elif self.body_plan == 3:
           self.description = self.kingdom + '-' + 'Body plan 3'
        elif sqelvod4:
            sbodiy_plelf.descriIpjn = seTf.kin +'-' ' while Body= 7 ...'
```

- **Evaluated and executed** (branch 3): condition and body both pristine.
- **Evaluated but not executed** (branches 1 and 2): the *conditions* survive intact,
  because they are still evaluated every run and a syntax error there is fatal. The
  *bodies* are destroyed, because they never execute.
- **Never evaluated at all** (branches 4 to 9): conditions and bodies both destroyed.
  Once branch 3 matches, Python stops evaluating, so `elif sqelvod4:` costs nothing.

The middle tier is the interesting one for a working engineer. Those lines are executed
in the sense that the interpreter reads and evaluates them, they show as covered by
some tooling, and their contents are still entirely unprotected.

### D3. Deletion slows growth but does not stop it, and raises acceptance

Adding deletion and duplication changes both numbers, in the same direction every time.

Final size falls substantially. On `hello_world_untested`, growth drops from 20.8x to
14.2x (938 bytes down to 640). On `beak`, from 2.3x to 1.2x. But growth never becomes
shrinkage, because the three insert-type operators still dominate. This is the measured
basis for the correction recorded in A3.

Acceptance rate *rises* in every single experiment, most sharply on `abiogenesis`
(17.5% to 40.4%). Deleting accumulated junk is usually harmless, so more mutations
survive selection once deletion is available. That was not predicted.

### D4. The beak digit is never hit

Across five seeds and 5000 total generations, the `9` in `beak.py` was never changed to
another digit. Accepted mutations were whitespace and layout only. See A1.

---

## Section C. Original text, unaltered

The following is the original wiki page as published, preserved verbatim. Image links
are retained as they appeared and are known to be broken (see A5); regenerated text
diffs are in [`diffs/`](artifacts-2016/diffs/).

---

# Mutating Source Code

I've been writing computer source code since about 1978, around age 7.  I went to college, got my bachelor's degree in Computer Information Systems in 1992, and have worked as a software engineer ever since.

Over the years, I've found that it takes a lot of design, experience, and coordination to keep any codebase from deteriorating as software engineers touch it.  I've also found that making elegant systems takes a lot of forward-looking strategic effort.  When I heard that blind random mutations and natural selection caused elegant interconnected systems to come into being, my instincts told me that wasn't possible.  I decided to write a code "mutator" that prepends, appends, overwrites, and inserts a mix of characters and python keywords to Python programs to see if my instincts were right or wrong.

In addition to the mutator, I also needed to create a selector to choose the acceptable mutations.  There are a few levels of selectors.  One is just seeing if the code will compile.  Another more difficult selector I added was a suite of unit tests that explicitly test certain functionality against expected outputs.  The third selector tests the code's validity and readability/maintainability – a program called pylint.

I found that my instincts were correct.  Not only did random mutation and selection of computer code not have creative power, but they were also highly destructive.  The only way for these programs to survive was to have strong enough selectors to protect the vital parts of the code.  Any portion of the code that selectors didn't protect was utterly destroyed.  I have included some preliminary examples below.

Mathematically this makes complete sense.  There are practically infinite ways to arrange the characters that make up a program and only a comparatively tiny subset of those that are valid.  An even smaller subset of those would do anything useful.  And an even smaller subset would do it elegantly with many parts working together to achieve an end result.  Random mutations are so much more likely to find a useless change than a useful change that they end up destroying any pre-existing order.  For example, the tiny hello world example below has about 1.08e+70 possible combinations of characters that could make up a program of that length.  That's about 36 different characters to the 45th power, which is the length of the program.  The human genome contains about 3.5 billion of 4 possible characters, which is 4 to the power of over 3 billion, which is practically infinite.  For comparison, there are only 10 to the 80th power of atoms in the known universe.  The numbers here are beyond astronomical, and these mathematical models support that random mutation should exhibit only destructive power at any significant scale.

Note that I'm not trying to simulate any biological processes here.  I'm just testing the informational premises underlying mutation and selection and have tried to pick the simplest examples to demonstrate these mechanisms' true nature.  The examples below use a program that visually shows the differences between files - often called a diff program.  Programmers use these to see what has changed over time in a program.

There are roughly 35 to 40 different 8-bit characters used in the program examples below.  In biology, 4 different base pairs combine in triplets to map to one of 20 amino acids that link together to create proteins.  My characters use 8 bits, 256 possible combinations, so I'm using a subset of the total possible characters.  The 4-base triplets have 64 possible combinations, which redundantly map to one of 20 amino acids.  So the mechanics are similar but not identical in scale between bases/bits and triplets mapped to characters/amino acids to make up programs/proteins.

## Hello World - untested

*(image broken, see [`artifacts-2016/diffs/hello_world_untested.diff`](artifacts-2016/diffs/hello_world_untested.diff))*

The image above shows the differences between the starting point of the untested hello world program (on the left) and the final state of it after 1000 generations (mutations) (on the right).  This program had no unit tests, so all that was tested is that it could be executed and wouldn't return an error because of syntax errors or other errors.

There were only a few elements that survived.  The first was the word **def**, a python keyword used to define a function.  Mutate a letter of that word, and it turns into a syntax error – a fatal mutation.  The second item was the first and second pairs of parenthesis.  I was surprised to see these survive until I realized that the other would be unbalanced if only one got mutated and cause a syntax error.  So pairs of things survive mutation.  The colon at the end of the "def" line is the third thing that survived.  Thinking about it now, it's actually paired with the "def" keyword.  If either one is destroyed, the other becomes unbalanced, and you get a syntax error.  The same pairing concept also applies to the single quotes around the string literal.

The parts that were destroyed were just as interesting.  The numbers at the start and end of the program are valid Python, but they do nothing at all.  Some of these numbers managed to get a "J" suffix, which indicates that they are imaginary literals.  One even has "%" signs embedded in it.  This is the modulus operator, which returns the remainder of a division operation.  Again, doing this operation on a number on a line by itself is valid but accomplishes nothing.  The function name is destroyed since Python doesn't care what you call your functions.  A parameter "EL" was then added to the function that initially didn't take a parameter.  This new parameter is not used within the function, which is valid unless you run pylint against it, which will complain about it.  I wasn't using pylint on this experiment.  Next, the "return" was destroyed and replaced with a garbage function call.  I was initially surprised by this, but then realized that this wouldn't cause a compile-time error, but a run-time error only if this hello_world function was actually called by something, which in the untested case, it isn't.  Of course, the text being returned is also destroyed since Python doesn't care about the content of strings except in some special cases – this string not being one of those cases.

So without tests to check what this program is doing, it gets destroyed.

## Hello World – tested

*(image broken, see [`artifacts-2016/diffs/hello_world_tested.diff`](artifacts-2016/diffs/hello_world_tested.diff))*

This looks much better.  The unit test for this hello world program calls the function named hello_world() and then verifies that the text returned is "Hello World!".  Just doing that causes a lot of things to change from the untested version.

There are still random numbers above and below the function, which affect nothing.  The name of the function is immutable because if it ever gets mutated, the unit tests will not find the function, and they will therefore fail, and the mutation will be rejected.

No parameter was added to the function because such a parameter isn't optional.  And since the unit test doesn't pass in a parameter, the unit test would fail, and the mutation would be rejected.

The "return" and the text in quotes remain unchanged because either of those being changed would cause the unit test to fail.  There was an "R" inserted before the quoted string, which, in Python, indicates that the text inside the string is to be taken literally and escape characters like backslashes are to be taken literally.  Since there are no escape characters inside the string, this mutation did not affect the string being returned and therefore was accepted.  There was also a newline character inserted before the closing parenthesis, which has no effect on the code's operation but makes it less readable.  Once I add pylint to the test suite, I believe most of these mutations will become impossible since they all degrade the quality, readability, and maintainability of the code.

*(image broken: Hello World, tested and pylinted)*

Here we have the pylint-constricted test that looks worse in some ways and better in others.  To get a score of 10 out of 10 from pylint, you must have module- and function-level docstrings, which are the strings you see at the top of the file and within the function itself that start and end with triple quotes, which are multi-line strings in Python.  These got destroyed, and so that's the main regression with the pylint test.  The unit test to check the phrase returned is still in place.

Notice that the random numbers are gone.  They are rejected by pylint as being "pointless statements" and are therefore rejected.  The docstrings are destroyed completely as they aren't held in place by any unit tests.

Notice the top docstring has had its triple quote (""") mutated into U"h"" which works since the prefix "U" means the string is Unicode, then the first quote makes this a normal string, and the next quote ends that string of "h", then the next quote starts a new string which ends as the first quote of the triple quote, then the two quotes after that are just an empty string.  This isn't very important, just interesting that this paired item (opening and closing triple quotes) could be mutated because they can be split up and still work, unlike single quotes, or parenthesis, which are just single characters and can't be split.

Pylint also prevented any lines from getting "too long" and held the number of newlines between certain parts of the code to acceptable numbers of newlines.

In summary, pylint prevented the numeric garbage from happening and kept line lengths from growing too far, and that's about it.

## Abiogenesis - untested

*(image broken, see [`artifacts-2016/diffs/abiogenesis.diff`](artifacts-2016/diffs/abiogenesis.diff))*

I decided to start with an empty file and see what would grow.  Since I wasn't sure what to test, I didn't add a test to this one.  I could have written a test to see if a self-replicating program appeared with many functions that work together to reproduce itself - like what would be necessary for a cell to emerge before it could replicate itself - but my instincts are that any such test would prevent any mutation that didn't produce something functional right off the bat.  I'd end up with an empty file.  And really, without replication, there are no tests.  No replication means no natural selection, which means no tests.

Again we see here that numeric constants can appear.  These constants do nothing and are functionally equivalent to an empty file.  Some "J" suffixes crept in, and some "%" modulus operators did as well.  I ran another version of the mutator that inserts Python keywords and random characters and had a similar result but with a few "or" and "and" statements thrown into the middle of the random numbers.

So the only thing allowed to grow was something random that didn't actually do anything productive.

## Beak Length - tested

*(image broken, diff is empty; see correction [A1](#a1-the-beak-result-is-genetic-drift-not-adaptation))*

I wanted to test if adaptation could occur by mutating an already existing "knob" like beak length.  Assume that shorter beak lengths will survive better than longer beak lengths and that anything over length 9 will be selected out.  The unit test lets any beak length 9 or under live and kills off anything larger.  In one of the tests, I got a beak length of 3 to live (the 9 was overwritten with a 3).  Nothing else interesting happened as the rest of the mutations proved fatal by breaking the unit test or invalidating syntax.  Adaptation works.

> **See correction A1.** This is drift under a ceiling, not adaptation, and the committed
> artifact does not reproduce it.

## Multiple interdependent functions - tested

*(image broken, see [`artifacts-2016/diffs/multiple_functions.diff`](artifacts-2016/diffs/multiple_functions.diff))*

Since unit tests are a form of pairs of things that work interdependently and protect each other from mutations, I decided to write a slightly more complex program with 4 functions in it.  The fourth function calling each of the three other functions to get information from them and return the combined result of them.  The unit test tested each of the three functions to ensure they returned the correct intermediate result and tested the fourth function's result, which is redundant.

The results were as expected.  No mutations that broke syntax or broke any intermediate or final result were allowed, leaving a tiny target for successful mutations.  The familiar random numbers at the beginning and end of the program crept in, and a couple of newline characters placed where they had no effect also crept in.

## Body Plans - tested

*(image broken, see [`artifacts-2016/diffs/body_plans.diff`](artifacts-2016/diffs/body_plans.diff))*

I recently heard a theory around multiple body plans being inside of a single genome.  One possible method for many different body plans to emerge in a relatively short amount of time was for these body plans to be switched on rather than evolving into each other.  I decided to see how information in such a situation would behave.

I assumed that some parts of the genome were common between the body plans and other parts were different between the body plans, and so I made a base class with some common information in the form of the word "Animal".  I then allowed 9 body plans to exist and selected one of them to be currently active – number 3 of 9.  Then I started mutating the code.  The unit tests just made sure that any one of the 9 body plans was returned.  If body plan 3 got switched to body plan 7 - as long as body plan 7 was not destroyed by mutation - it would pass the test just fine.

The unit test held both the common "Animal" text and the currently selected body plan (number 3) in place.  The rest of the body plans' information was destroyed since those body plans weren't interacting with the unit tests, and so mutations were allowed to destroy them.  The selected body plan was never allowed to switch (i.e., from 3 to 7, for example) since switching to one of the deselected body plans would return the garbage data that had been mutated in that deselected body plan.

Notice that the if (or elif, short for "else if") statements for body plans before number 3 are protected against mutation since the interpreter goes through them in order, and syntax errors there would be rejected.  Notice, however, that the elif statements below body plan 3 were destroyed.  This was allowed because once body plan 3 matched, it stopped evaluating the rest of the if statements, so they could contain runtime errors without breaking anything.  This is similar to the mechanism that allows a "0 and …" to grow very long on a single line during mutation because after you evaluate "0 and" you don't have to evaluate the rest of the line since you already know 0 AND anything is going to return false.  This is called short circuit evaluation, and it prevents the parts of the code that are not evaluated to be mutated.  The double equal signs and the numbers, elif's, and colons were protected by their pairing and probably by the small target that single digits are – comparing the size of a single digit to the overall size of the code.

The exception raised on an invalid body plan also got mutated to the point of dysfunction except for the "raise" keyword and the usual suspects of paired keywords/symbols like parenthesis, quotes, etc.  This experiment also suffered from the commonly seen garbage numbers at the top and bottom of the file.

Below is the code coverage for a body plans mutation run.  Notice the lines that got coverage in the unit tests (green) are the sane lines, and the lines without unit test coverage (red) are the insane lines:

*(image broken: code coverage screenshot)*

## English – tested

*(image broken, see [`artifacts-2016/diffs/english.diff`](artifacts-2016/diffs/english.diff))*

Next up is the mutation of an English sentence.  The starting point for our sentence is from Shakespeare.  The ending point is not.  The unit test for this one just checks to see if the mutation caused a spelling error or not.  If it did, the mutation is rejected.  If the words are all still valid, it accepts it.  "The" was turned into ":De" – yeah, de is in the dictionary I found online, and punctuation is ignored in the test, so some words might gain a colon or other punctuation marks.  "he" was changed into "MD".  "is" was turned into "iS" which is a clever coincidence to change the case of a letter.  "Wise" was changed to "wide".  "The" was appended to be "theM".  The second "wise" in the sentence was turned into "wiRe", which breaks the connection the two "wises" had in the beginning.  "Man" was turned into "wan".  "to" became "tAp".  "be" became "EeL".  "fool" gained a colon as well.

The meaning of the original sentence has been lost in just 1000 generations.  91 mutations were accepted.  Several mutations were spent making the garbage numbers before and after the quote line.  I plan to add some grammar checking to see if we can keep a valid sentence structure intact.  If we can, I'm not sure how I'd evaluate whether the sentence was "better" than the original or had gained some form of useful information above the original.

It's interesting to note that the modifications being made in these examples modify the medium that information is flowing through between a human programmer and a computing device or between one mind and another mind.  Normally, to alter ideas or create new ideas, that's not done using the medium that the ideas are traveling through.  It's done in someone's mind with a goal and purpose, which is then encoded into the medium used to deliver the idea.  Trying to get new ideas by tampering with the medium itself is somewhat backward.

## Next steps

I have several ideas about new tests I'd like to run:

1.  I'm in the process of creating self-replicating code that will procreate and compete with other offspring for limited resources, etc., to see if that type of environment changes the nature of what random mutation and selection can do.  See [issue #11](https://github.com/rcronk/mutate/issues/11) for more detail.  So far, the preliminary tests show the same kinds of useless garbage mutations as the tests above.

1.  I would also like to perform more advanced grammar tests on the English test to see if the English sentence information content or validity could be preserved.

1.  Continue enhancing the mutator to allow for other types of mutations, including duplication of parts of the code, deletions or truncations of parts of the code, keyword or operator pairs instead of single mutations, etc.  It can currently prepend, append, insert, and overwrite with a 25% chance of occurring.  Once I've added other kinds of mutation, I would like to adjust the mutation type probability to match DNA mutation.

1.  I would like to try unit tests that can guide code to a desired result to see if that's possible – kind of a more robust form of the adaptation idea presented above.

As I perform each test and see the results, it gives me more ideas for future tests.

## Conclusion

So far, my intuition has been confirmed by these initial test results: random mutation and selection were not shown to have creative power and, in fact, showed only destructive (breakage) or wasteful power (in the case of random numbers appearing).  The destruction occurred at different levels: in the syntax itself, in the information represented by that syntax, and the design behind achieving the desired result.  Selection only helps protect the code from accepting mutations, protecting the original code from being destroyed.  It seems that if anything could be created through this process, the resulting information would have to come from the environment/selection, not through the mutation.  But the environment doesn't care about internal organs.  It just cares about surface interactions between the creature and the environment, like the unit test testing external interfaces.

---

## Section D. Known code defects in this directory

Preserved as-is; not fixed, since this code is archived.

- **`self_mutator.py` does not run.** It is a partial merge of the file-mutator class with
  a new organism lifecycle. `main()` references `args.creature`, which `argparse` never
  defines. `save_mutant()` and `mutate()` reference `self.mutant_path`,
  `self.test_path`, and `self.creature_content`, none of which the rewritten `__init__`
  sets. `Dictionary` was dropped from this module but `test_english.py` still imports
  `mutate.Dictionary`.
- **Hardcoded Windows path.** `save_mutant()` builds `'__pycache__\\%s.cpython-35.pyc'`,
  which is a no-op on Linux and macOS and assumes Python 3.5.
- **Hardcoded `python` interpreter.** `subprocess.call(['python', cmd])` assumes `python`
  resolves to Python 3.
- **`_flawed_copy` has no deletion operator.** See correction A3.
