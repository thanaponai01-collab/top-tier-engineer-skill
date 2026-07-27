---
name: structure-gate
description: >
  Measure the structural shape of a codebase — complexity, nesting, function/file
  length, import cycles, duplication — and report whether it reads as spaghetti, in
  plain language a non-coder can act on. Use whenever the user asks "is this code a
  mess / spaghetti / maintainable", whenever a build session completes and the
  director cannot personally read the result, and as the automatic structural floor
  in CI. This is the measurement counterpart to senior-review: that skill judges
  whether the code is WISE; this one measures whether its SHAPE is sound, with
  numbers, and never decides wisdom itself.
---

# Structure Gate

> **Wiring** — Service skill, callable from any stage and runnable unattended in CI.
> Consumes: a codebase (or a slice's changed files), plus the accepted baseline when one
> exists. Produces: the structural report + `STRUCTURE_REPORT.md`, the structural baseline,
> `DEBT_LEDGER.md` (this skill owns it), and a `STRUCTURE` verdict line. Mandate within the suite:
> `senior-review` asks *"is this codebase wise?"* and mentors; `correctness-gate`
> asks *"is it provably right?"*; this skill asks **"what is its measured shape, and
> does that shape read as spaghetti?"** — it produces numbers, not judgement, and
> routes every breach to `senior-review`/`scrutinize` for the wisdom call rather than
> condemning it. Findings route onward: structural flags → `senior-review` or
> `scrutinize`; an import cycle that reveals a layering error → `arch-design`; a
> god-file that is really a missing module boundary → `arch-design`. Distinct from
> `wire-check` (that asks *"is it connected?"*, this asks *"is it tangled?"*) and from
> `latent-audit` (that asks *"is it dead or pointed the wrong way?"* — same import graph,
> different question; layer-direction breaches and deletion manifests are its mandate, not this one's). Shared
> vocabulary and laws: `PROTOCOL.md` at the suite root — authoritative when present.
> (Gloss: **(proven)** executed · **(trace-only)** read, chain complete ·
> **(suspected)** chain incomplete, flag only · **(assumed)** unverified premise.)

The director who cannot read code has no instinct for spaghetti. This skill is the
instrument that gives them one: it measures the few structural signals that
correlate with unmaintainable code and reports them as a plain verdict, so "the
code got tangled" stops being invisible.

## Operating contract

1. **Measure, never judge.** Every number this skill emits is **(proven)** — a real
   measurement over real source. But a measurement is not a verdict on wisdom: a
   breach means *a reviewer should look*, never *the author was wrong*. Chesterton's
   Fence (Law 3): an odd long function may be the right call; this skill flags it for
   `senior-review`, it does not condemn it. The instant this skill starts deciding
   wisdom, it has stolen `senior-review`'s mandate — refuse that.
2. **Plain language is the deliverable.** The audience is a director who cannot read
   the source. "complexity 17" is not the output; "TANGLED — three functions are
   hardest-to-test branch-heavy code, a reviewer should look" is. Numbers back the
   words; the words are the product.
3. **Derive the toolchain from the codebase.** Carry no fixed linter. Identify the
   languages present and run the deepest analysis available for each: the suite ships
   `tools/structure-report.py` (stdlib, Python-deep + language-agnostic line/dup
   signals); if richer linters are installed (radon, ruff, eslint, madge) note them
   and escalate. Say honestly where depth stops — a Python-deep, JS-shallow report is
   reported as exactly that, never dressed up as uniform.
4. **A breach gets a category, a location, and a route.** Report *which* signal
   tripped, *where*, and *which skill owns the follow-up* — never a bare number with
   no next step.
5. **Measure direction, not only level** (PROTOCOL §10, the ratchet rule). A gate that
   re-asks "is this file too long?" every run gets the same defensible "justified" every
   run and converges on permanent acceptance while the file triples. Once a codebase has
   accepted debt, this skill's operative question changes from *"is this bad?"* to
   **"did it get worse?"** — which is still a measurement, so Law 3, violation ≠
   deviation, is untouched: the accepted breach is never called wrong, only forbidden to
   grow. This skill is the only one that can see accumulation, so it is the only one that
   can stop it.

## Procedure

### 1. Census
Identify languages and entry points; pick the analysis depth available per language
(contract rule 3). Note which languages get deep vs. shallow treatment. Check for an
existing baseline (`.structure-baseline.json`) and `DEBT_LEDGER.md` — their presence
decides whether step 3 runs in level mode or ratchet mode.

### 2. Measure
Run `tools/structure-report.py` over the target (whole repo, or a slice's changed
files for a fast inner-loop check). The signals and why each is a spaghetti tell:

| Signal | Spaghetti meaning |
|---|---|
| Cyclomatic complexity | branch density — the best-studied bug predictor |
| Nesting depth | the literal visual shape of spaghetti |
| Function length | one function doing too much, resists testing |
| File length | god-files concentrate risk and merge pain |
| Import cycles | circular deps — a graph you can't reason about in isolation |
| Duplication | copy-paste blocks drift apart and rot independently |
| Opaque code | a large region the parser never entered that is shaped like code — invisible to every signal above, and **untestable by construction** (PROTOCOL §10 rules 5–7) |

**Report coverage before findings, always** (§10 rule 5). A finding count is not a
result without the denominator it was measured over. A region the analyzer never
entered contributes zero to every signal, and every one of those zeros is correct — so
the more of a subject is invisible, the cleaner its report looks. State on every run
what fraction was actually entered, and report what you could not enter as UNKNOWN
rather than omitting it, because an omitted region reads exactly like a clean one.

**Find the unentered regions by structure, never by vocabulary** (§10 rule 6). Do not
ask which known language a region contains — that is knowledge of the languages you
happen to know, and it dates on contact with the next one. Ask the language's own
lexer which tokens it classified as non-code (exact, free, and true in every language),
then discriminate what is inside by content-free shape statistics, because code is a
*tree of varied statements* while prose is a uniform stream and tabular data is uniform
rows. Exempt only what the language itself declares as documentation. Watch for the
same bug one level down: a statistic can look content-free and still encode one syntax
family's habits, so calibrate against fixtures from unlike families.

Report a hit as a **testability** finding, not a style one: no test harness can address
code that is unreachable by construction, so the absence of tests there is not a
coverage gap `correctness-gate` failed to report — it is a shape `correctness-gate` was
never able to see, which is why this skill owns it.

### 3. Ratchet, or set the baseline
- **No baseline yet, findings present.** Do not treat the list as a sentence on the
  author — it is a starting position. Record it (`--write-baseline`), open a
  `DEBT_LEDGER.md` row per file, and say plainly that the debt is now frozen where it
  stands. This is also what makes the gate usable on legacy code at all: an
  un-baselined legacy run is red forever, and a permanently-red gate is a disabled gate.
- **Baseline present.** Run `--baseline` (add `--require-debt-ledger` in CI). Report
  only what is *new*, *worse*, or *repaid*; accepted-and-unchanged debt is noise.
- **Never re-baseline to clear a regression** (§10 rule 3) — that is the single move
  that disables the ratchet, and it is the structural analogue of weakening a proof
  line to pass it. A baseline is regenerated when debt is **repaid**.

### 4. Debt ledger
Own and maintain `DEBT_LEDGER.md`. One row per accepted breach:

`ID | file/symbol | signal + measured value | why accepted | cost per future change that touches it | repayment trigger | date`

The **repayment trigger** is mandatory and follows `TODO_LEDGER.md`'s rule — a deferral
with no trigger is a wish. A trigger must be an *observable event*, not a date or an
intention, so that whether it has fired is a matter of fact rather than of will.

The **cost** column is what makes debt legible to a director who cannot read the
source. State it as a price paid per future change, in the units that director already
cares about — effort, risk, or what becomes impossible — never as a property of the
code. "This file is long" is a fact about the source and means nothing to them; what
the next change to it will cost, and what cannot be verified about it afterwards, is a
decision they can actually make.

### 5. Verdict and route
Emit the plain-language report and exactly one `STRUCTURE` verdict line. For each
breach, name the owning skill for the wisdom call (rule 4). Write
`STRUCTURE_REPORT.md` for the handoff trail. A `regressed` verdict routes to
`build-discipline` (carrying capacity, §10 rule 4) as well as to the wisdom reviewers.

## Verdict line (PROTOCOL §5)

```
STRUCTURE: clean(N files, M functions scanned)
STRUCTURE: findings(top: <worst signal>, count: K) | review-needed
STRUCTURE: held(accepted: K, repaid: R)
STRUCTURE: regressed(new: A, worse: B, top: <signal>) | review-needed
STRUCTURE: blocked(no analyzable source found)
```

A `findings` verdict is **not** a fail of the author — it is a routed request for a
wisdom review. Only `senior-review`/`scrutinize` turn a structural flag into a
defect, and only after refuting the Chesterton's-Fence case for it. A `regressed`
verdict is different in kind and needs no wisdom call to stand: it reports that a
number the project already agreed to freeze has moved, which is a fact, not a
judgement. `held` is the healthy steady state on a codebase with known debt — it does
not claim the codebase is clean, only that it did not get worse.

## Boundary

This skill stops at *shape*. Whether a flagged shape is acceptable is
`senior-review`'s call; whether the code is correct is `correctness-gate`'s; whether
it is connected is `wire-check`'s. If this skill ever starts ruling on wisdom,
correctness, or connectedness, it has overrun its mandate and the overreach is a
defect in this skill.
