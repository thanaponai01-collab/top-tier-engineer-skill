---
name: structure-gate
description: Measure a codebase's structural shape (complexity, nesting, function and file length, import cycles, duplication) and say in plain words whether it reads as spaghetti and whether it got worse. Use for "is this code a mess / spaghetti?" or as a CI structural check.
---

# Structure Gate

Someone who can't read code has no way to feel it getting tangled. This skill measures the few
structural signals that go with hard-to-maintain code and reports them in plain words.

## Rules

1. **Measure, don't judge.** A number over threshold means *someone should look*, never *the author
   was wrong*. A long function may be the right call.
2. **Plain language is the product.** Not "complexity 17", but "three functions have so many
   branches they're the hardest part of this codebase to test". Numbers back the words.
3. **Use the best tool available per language.** The bundled script is deep on Python and gives
   line and duplication signals for any language. If better linters are installed (radon, ruff,
   eslint, madge), use them too. Say where depth runs out: deep on Python, shallow on JS, says so.
4. **Report how much you actually measured, before findings.** Code the analyzer couldn't enter
   scores zero on every signal, so the more is invisible, the cleaner it looks. Report what you
   couldn't enter as UNKNOWN, never as clean.

## Procedure

### 1. Take stock
Find the languages and pick the deepest analysis for each.

### 2. Measure
Run the bundled script (in this skill's `scripts/` folder; stdlib Python, no install):

```
python <this skill's base directory>/scripts/structure-report.py <paths>          # human report
python <this skill's base directory>/scripts/structure-report.py --json <paths>   # machine-readable
```

| Signal | Why it matters |
|---|---|
| Cyclomatic complexity | number of branches; the best-studied predictor of bugs |
| Nesting depth | what tangled code looks like |
| Function length | one function doing too much, hard to test |
| File length | concentrates risk and merge conflicts |
| Import cycles | modules that can't be understood alone |
| Duplication | copies drift apart and rot separately |
| Opaque code | large code-shaped regions the parser never entered (e.g. code in strings): invisible to every other signal and impossible to test |

### 3. Track direction (optional, for existing codebases)
On an old codebase, a fixed threshold is red forever and gets ignored. Freeze today's breaches and
only fail on things that get worse:

```
python scripts/structure-report.py --write-baseline .structure-baseline.json <paths>
python scripts/structure-report.py --baseline .structure-baseline.json <paths>
```

With a baseline, report only what's new, worse, or repaid. **Never regenerate the baseline to clear
a regression**; regenerate it when debt has actually been paid down. A debt worth explaining gets
a one-line comment at the code, where the next reader will see it.

## Report

- Open with the plain answer: does it read as spaghetti, yes / in places / no.
- What fraction of the code was measured, and whether the shape is getting better or worse.
- One row per finding: signal, where (`file:function`), measured value, what it costs the next
  person who changes it (effort, risk, what can't be tested). "This file is long" means nothing to
  a non-coder; "every change here risks breaking checkout and can't be tested in isolation" does.
- Raw script output after.

This skill stops at shape. Whether a flagged shape is acceptable, correct, or connected is a
separate question.

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.
