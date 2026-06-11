# Changelog

Skill files are versioned artifacts (meta-skills Discipline 5). Changes are recorded here;
superseded behavior is described, never erased.

## 1.3.1 — 2026-06-11

**Fresh-eyes rule (PROTOCOL §8)** — separation of duties for review-class skills. When the
session that built a change runs `senior-review` or `scrutinize` on it, and stakes warrant, the
review runs in a fresh context (subagent / new session) from artifacts alone — never the build
conversation. Below the stakes bar, same-context review is legal but explicitly marked. A fresh
reviewer who cannot operate from artifacts alone has found a Law 2 defect by that fact alone.
Pointer lines added to both review skills. Closes the self-review blindness gap; the remaining
known gaps (no live run yet; prose without mechanical enforcement; nothing past "ship") are
recorded as the suite's own residual-risk statement below.

**Residual risk, stated honestly:** every claim that this suite *works* is (trace-only) until a
real project runs the full lifecycle. The next change to these files should be driven by that
run's level-2 postmortem (Discipline 5), not by further design.

## 1.3.0 — 2026-06-11

**Twelfth skill: `scrutinize`** — change-scoped, outsider second opinion on any not-yet-landed
delta (plan, design doc, PR, diff). Owns the previously unowned question "should this change
exist, and does it do what it claims?" Adapted from an external skill and conformed to suite law:
- Wiring block (consumes/produces/handoffs) — it arrived as an orphan skill.
- Informal claim-vs-verification rule replaced by the evidence vocabulary; cheap-execution
  escalation made binding.
- Its simpler-alternative pass now operationalizes meta-skills Discipline 7 (pointer, not a
  second statement, per Law 1).
- Law 3 guard on the outsider stance + mandatory ledger check (explained surprises are
  archaeology, not signal).
- Registry verdict line `SCRUTINY:` with a new `blocked(underspecified)` state; PROTOCOL §4/§5
  rows added; chief-engineer review routing split cleanly between senior-review (codebase) and
  scrutinize (delta); senior-review's wiring block states the boundary from its side.

## 1.2.0 — 2026-06-11

**The taste layer** — rigor was covered; these encode the instincts of great engineers:
- `meta-skills` Discipline 7 — Simplicity: the subtraction pass; complexity must be purchased by
  an invariant or measurement; abstractions on second use; deletion is a recorded win.
- `arch-design` — the dependency bar: a library enters only with build-it-ourselves cost,
  surface-used fraction, maintenance pulse, and a pin plan; default to writing small things.
- `chief-engineer` — spike mode: declared, timeboxed, quarantined throwaway exploration whose only
  durable output is knowledge in a ledger; spike code never graduates by merge. New routing row.
- `build-discipline` — smallest diff that satisfies the proof line (Phase 2); the short leash:
  full diff self-review before every commit, mandatory for generated code (Phase 5).
- `correctness-gate` — "look at the real thing": read actual outputs for real inputs, paste one
  representative pair into the verdict.

## 1.1.0 — 2026-06-11

**Wiring of the suite itself**
- `PROTOCOL.md` §0: where the suite root is from inside any install, and what "invoking a skill"
  means (open its SKILL.md, execute the contract; fall back to the §4 registry if absent).
- `chief-engineer` Phase 0: locate-and-load mechanics, stated where the router actually runs.
- `README.md`: CLAUDE.md bootstrap block so governed projects auto-route fresh sessions.

**Scaling mechanism (replaces the unenforced "lightweight by default" promise)**
- `PROTOCOL.md` §7: the scale rule — ledgers become files only when memory must outlive the
  session; otherwise inline under the ledger's heading, promotable verbatim.
- `chief-engineer`: concrete fast-path definition; two new routing rows (pure questions →
  no lifecycle; no-owner requests → named, never silently absorbed).

**Law 1 conformance**
- Decay rule was stated three times (PROTOCOL §1, build-discipline, meta-skills); now stated once
  with pointer-with-fallback references.
- Dangling bare-number Law references in debug-protocol now carry names; PROTOCOL §6 forbids bare
  numbers going forward.
- Evidence-tag glosses had drifted (three skills omitted **(suspected)**); PROTOCOL §6 now defines
  one canonical gloss, copied verbatim.

**Greppability**
- PROTOCOL §5 now carries the full verdict-line registry (all ten nouns + states) so one grep
  recovers any run's trajectory from a transcript.

## 1.0.0

Initial wired suite: eleven skills, PROTOCOL, MAP, plugin manifest.
