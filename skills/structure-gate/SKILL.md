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
> Consumes: a codebase (or a slice's changed files). Produces: the structural report
> + `STRUCTURE_REPORT.md`, and a `STRUCTURE` verdict line. Mandate within the suite:
> `senior-review` asks *"is this codebase wise?"* and mentors; `correctness-gate`
> asks *"is it provably right?"*; this skill asks **"what is its measured shape, and
> does that shape read as spaghetti?"** — it produces numbers, not judgement, and
> routes every breach to `senior-review`/`scrutinize` for the wisdom call rather than
> condemning it. Findings route onward: structural flags → `senior-review` or
> `scrutinize`; an import cycle that reveals a layering error → `arch-design`; a
> god-file that is really a missing module boundary → `arch-design`. Distinct from
> `wire-check` (that asks *"is it connected?"*, this asks *"is it tangled?"*). Shared
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

## Procedure

### 1. Census
Identify languages and entry points; pick the analysis depth available per language
(contract rule 3). Note which languages get deep vs. shallow treatment.

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

### 3. Verdict and route
Emit the plain-language report and exactly one `STRUCTURE` verdict line. For each
breach, name the owning skill for the wisdom call (rule 4). Write
`STRUCTURE_REPORT.md` for the handoff trail.

## Verdict line (PROTOCOL §5)

```
STRUCTURE: clean(N files, M functions scanned)
STRUCTURE: findings(top: <worst signal>, count: K) | review-needed
STRUCTURE: blocked(no analyzable source found)
```

A `findings` verdict is **not** a fail of the author — it is a routed request for a
wisdom review. Only `senior-review`/`scrutinize` turn a structural flag into a
defect, and only after refuting the Chesterton's-Fence case for it.

## Boundary

This skill stops at *shape*. Whether a flagged shape is acceptable is
`senior-review`'s call; whether the code is correct is `correctness-gate`'s; whether
it is connected is `wire-check`'s. If this skill ever starts ruling on wisdom,
correctness, or connectedness, it has overrun its mandate and the overreach is a
defect in this skill.
