---
name: structure-gate
description: >
  Measure a codebase's structural shape — complexity, nesting, function/file length, import cycles, duplication — and report whether it reads as spaghetti, in plain language. Use for "is this code a mess/spaghetti", or as the CI structural floor.
---

# Structure Gate

> **The question:** What do the numbers say about its shape — is it tangled, and did it get worse?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

A director who cannot read code has no way to feel that the code is getting tangled.
This skill is the instrument that gives them one: it measures the few structural
signals that go with hard-to-maintain code and reports them in plain words, so "the
code got tangled" stops being invisible.

## The job

1. **Measure, never judge.** Every number this skill reports is **(proven)** — a real
   measurement over real source. But a measurement is not a judgment on the design: a
   number over threshold means *a reviewer should look*, never *the author was wrong*.
   Law 3 applies: an unusually long function may be the right call; this skill flags it
   for `senior-review`, it does not condemn it. The moment this skill starts ruling on
   whether a design is good, it has taken `senior-review`'s job — don't.
2. **Plain language is what you deliver.** The reader is a director who cannot read
   the source. "complexity 17" is not the output; "TANGLED — three functions have so
   many branches they are the hardest part of this codebase to test; a reviewer should
   look" is. The numbers back up the words; the words are the product.
3. **Pick the tools from the codebase, don't bring your own.** Find which languages
   are present and run the deepest analysis available for each: this suite ships
   `tools/structure-report.py` (standard library only — deep on Python, plus line and
   duplication signals that work on any language). If better linters are installed
   (radon, ruff, eslint, madge), note them and use them. Say honestly where the depth
   runs out — a report that is deep on Python and shallow on JS says exactly that, and
   is never presented as even coverage.
4. **Every finding gets a kind, a place, and an owner.** Report *which* signal went
   over, *where*, and *which skill takes it from here* — never a bare number with no
   next step.
5. **Measure the direction, not just the level** (§8, the ratchet rule). A gate that
   asks "is this file too long?" every run gets the same defensible "yes, but it's
   justified" every run, and ends up accepting it permanently while the file triples in
   size. Once a codebase has accepted debt, the question this skill asks changes from
   *"is this bad?"* to **"did it get worse?"** — still a measurement, so Law 3 is
   untouched: the accepted problem is never called wrong, it is only forbidden to grow.
   This skill is the only one that can see things pile up, so it is the only one that
   can stop it.

## Procedure

### 1. Take stock
Find the languages and entry points, and pick the deepest analysis available for each
(rule 3 above). Note which languages get deep treatment and which get shallow. Check
whether a baseline (`.structure-baseline.json`) and a `DEBT_LEDGER.md` already exist —
that decides whether step 3 measures the level or measures the change.

### 2. Measure
Run `tools/structure-report.py` over the target (whole repo, or a slice's changed
files for a fast inner-loop check). The signals and why each is a spaghetti tell:

| Signal | Spaghetti meaning |
|---|---|
| Cyclomatic complexity | how many branches — the best-studied predictor of bugs |
| Nesting depth | how deeply indented the code gets; this is what tangled code looks like |
| Function length | one function doing too much, and hard to test as a result |
| File length | one huge file concentrates both risk and merge conflicts |
| Import cycles | modules that import each other in a loop; no part can be understood alone |
| Duplication | copy-pasted blocks drift apart and each rots separately |
| Opaque code | a large region the parser never got into that is shaped like code — invisible to every signal above, and **impossible to test at all** (§8 rules 5–7) |

**Always report how much you covered before you report findings** (§8 rule 5). A count
of findings means nothing without knowing how much was measured. A region the analyzer
never got into contributes zero to every signal, and each of those zeros is technically
correct — so the more of a codebase is invisible, the cleaner its report looks. On every
run, say what fraction you actually got into, and report what you could not get into as
UNKNOWN instead of leaving it out, because a region left out reads exactly like a clean
one.

**Find those regions by their shape, not by recognising the language** (§8 rule 6).
Don't ask which language a region is written in — that only works for the languages you
happen to know, and it goes stale the moment a new one appears. Ask the language's own
lexer which parts it classified as not-code (exact, free, and true in every language),
then tell what is inside apart using statistics about shape rather than content: code
is a *tree of varied statements*, while prose is an even stream of words and tabular
data is even rows. Exempt only what the language itself marks as documentation. Watch
for the same mistake one level down: a statistic can look content-free and still be
built on the habits of one family of syntax, so calibrate it against examples from
unlike families.

Report a hit as a **testability** finding, not a style one: no test can reach code that
is unreachable in principle, so the lack of tests there is not a coverage gap
`correctness-gate` failed to report — it is a shape `correctness-gate` was never able to
see, which is why this skill owns it.

### 3. Ratchet, or set the baseline
- **No baseline yet, and there are findings.** Don't treat the list as a verdict on the
  author — it is a starting point. Record it (`--write-baseline`), open a
  `DEBT_LEDGER.md` row per file, and say plainly that the debt is now frozen where it
  stands. This is also what makes the gate usable on old code at all: without a
  baseline, an old codebase is red forever, and a gate that is always red is a gate
  nobody looks at.
- **Baseline present.** Run `--baseline` (add `--require-debt-ledger` in CI). Report
  only what is *new*, *worse*, or *repaid*; accepted-and-unchanged debt is noise.
- **Never re-record the baseline to clear a regression** (§8 rule 3) — that one move
  disables the whole mechanism, and it is the same thing as weakening a proof line so it
  passes. You regenerate a baseline when debt has been **repaid**.

### 4. Debt ledger
Own and maintain `DEBT_LEDGER.md`. One row per accepted breach:

`ID | file/symbol | signal + measured value | why accepted | cost per future change that touches it | repayment trigger | date`

The **repayment trigger** is required, and follows build-discipline's rule for deferred
work — deferred work with no trigger is a wish. A trigger has to be an *event you can
observe*, not a date or an intention, so that whether it has happened is a fact rather
than a decision. Where the event is a number crossing a threshold, put it in the
baseline as `repay_at` instead of writing it in prose: `structure-report.py` then fires
the row itself, and the trigger no longer depends on someone re-reading this table at
the right moment.

The **cost** column is what makes debt mean something to a director who cannot read the
source. State it as a price paid on every future change, in terms they already care
about — effort, risk, or what becomes impossible — never as a property of the code.
"This file is long" is a fact about the source and means nothing to them; what the next
change to it will cost, and what can no longer be verified afterwards, is something they
can actually decide about.

### 5. Verdict and route
Shape and wording: `PROTOCOL.md` §9, ending in exactly one `STRUCTURE` verdict line (PROTOCOL §5).
The opening says what fraction of the codebase the tool could enter and whether the shape is getting
better or worse. The rows are the findings, one each, and each names the skill that owns the
judgment call (rule 4). Raw tool output goes under `Detail`. Write
`STRUCTURE_REPORT.md` only when PROTOCOL §3 calls for a file — otherwise the report
itself is the trail. A `regressed` finding goes to `build-discipline` (§8 rule 4) as
well as to the reviewers.

## Verdict line (PROTOCOL §5)

**Verdict noun:** `STRUCTURE`

```
STRUCTURE: clean(N files, M functions scanned)
STRUCTURE: clean(held: K accepted, R repaid)              [ratchet mode]
STRUCTURE: findings(top: <worst signal>, count: K)
STRUCTURE: findings(regressed: new A, worse B, top: <signal>)
STRUCTURE: findings(repayment-due: <id-hint>, <signal>, <current>/<threshold>)
STRUCTURE: blocked(no analyzable source found)
```

A `findings` verdict is **not** a mark against the author — it is a request for someone
to make a judgment call. Only `senior-review` or `scrutinize` can turn a structural flag
into a defect, and only after showing there was no good reason for it. A `regressed`
finding is a different thing and needs no judgment call: it reports that a number the
project already agreed to freeze has moved, which is a fact. `clean(held: …)` is the
normal healthy state for a codebase with known debt — it does not claim the codebase is
clean, only that it did not get worse.

## When not to use this

This skill stops at *shape*. Whether a flagged shape is acceptable is
`senior-review`'s call; whether the code is correct is `correctness-gate`'s; whether it
is connected is `wire-check`'s. If this skill ever starts ruling on design, correctness,
or connectedness, it has gone past what it covers, and that is a defect in this skill.
