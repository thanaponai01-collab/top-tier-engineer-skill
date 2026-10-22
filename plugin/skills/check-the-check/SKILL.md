---
name: check-the-check
description: >-
  Find out by running it whether a green test, suite or CI gate would actually catch a bug: plant
  one-line bugs, find tests that never run, and run a PR's new tests against the code before the
  change. Use when someone asks if green proves a feature works, if a suite or merge gate is strong
  enough, if a regression test proves the fix, or before signing off "covered by tests". Read-only.
  To write, repair or freeze checks, use verify-loop.
metadata:
  stage: assess
  card: "would this test catch a bug? find out by running it"
---

# Check the check

A green check proves only that it passed. Whether it would catch a bug is a separate question,
answered by watching it run against wrong code, never by reading it. The helper does that run, and
does it more thoroughly than hand-picked guesses:

```
python <skill-base>/scripts/check.py <repo> --check "<command that runs the check>" [--product FILE ...] [--base REF] [--json]
```

`<skill-base>` is this skill's folder. Run the command from the repo root, the way CI runs it (read
the CI file when one exists). Every run happens in a scratch copy under the system temp folder, so
the repo and its `git status` stay unchanged. Pass `--base <ref>` when the question is about a
change: a PR, a fix, a branch (`--base main`, or the merge base). `--product` defaults to the repo
code the check imports. Name it yourself for a non-Python check, or when the claim is about one file.

## Reading what it prints

| Line | Means | Your answer |
|---|---|---|
| `NEVER LOADED` | a test file the check command never imports (wrong name pattern, wrong folder) | what it covers is not covered by this check. Run that file directly and report what it shows |
| `NEVER RAN` | a test defined in a loaded file that never started (not a `TestCase`, misnamed, skipped) | same: it covers nothing until it runs |
| `HOLLOW` | the check imported product code but never called it | it passes without testing the product |
| `SURVIVED` | a one-line bug planted in the product, and the check still passed | judge each one (below) |
| `NEW TEST ... PASSES there` | a test added since `--base` passes on the old code | it cannot catch what the change fixed |
| `RUN FAIL` (verdict `red`) | the check fails now | report what fails; a red check is the answer, not a strength question |
| verdict `blocked` | the check could not run here | say so and where it does run; change nothing |

**Judge every survivor.** For each one, find an input whose result differs between the original
line and the mutated line, and say what the spec expects for that input. If such an input exists,
the survivor is a real gap: name the input, the right result and the wrong one that would pass.
If no input differs (for example `round(x, 3)` on a total that is rounded to the cent later
anyway), it changes nothing observable: say so in one line. `(that line never runs)` means no test
reaches that line at all.

When a finding points somewhere the helper cannot reach, such as a never-loaded file, a test that
only fails once it is collected, or code the check never imported, run that check yourself, in a
copy under the temp folder or with `git stash`, and restore everything before you answer.

## The answer

Answer the person's question first: yes, no, or which parts. Then give one line per finding:

- the gap, in the product's terms: "a $50.00 order is never tested", not "mutant 7 survived";
- the evidence you ran: the planted change and that the check stayed green, the base run, the
  test count;
- the test that would close it: input and expected result from the spec. Describe it; don't add it.

Also say which parts held: a rule the check caught when you broke it is covered. Never call a
check strong because it reads well, has many assertions or full line coverage. Full coverage only
means every line ran. Call it strong only when the helper says `strong`, or when every survivor
is judged as changing nothing.

## Guards

- Read-only. Do not edit, add or delete files in the repo, tests included. Scratch work goes in
  the system temp folder.
- Never weaken, skip or delete a check, even in a copy, to make a run go green.
- Your judgment of a survivor rests on what the spec says, not on what the code does.
- To fix the gaps, prove the result and keep that proof, hand off: load the verify-loop skill.
