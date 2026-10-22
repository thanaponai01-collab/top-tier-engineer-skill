# verify-loop design: one engine, two front doors, one call per question

## What the evidence says (2026-10-21/22 runs, Opus 5.5, 3 tries per arm)

| | Bare | verify-loop 1.18 | check-the-check 1.19 |
|---|---|---|---|
| Pass rate | 18/39 | 33/39 | 15/15 (bare 13/15) |
| Mean cost / try | $0.10 | $0.21 (2.1x) | $0.14 (1.4x) |
| Mean turns | 5 | 10 | 7 |

- verify-loop clearly helps on 7 cases. It adds nothing on 4 (`inherited-claim`,
  `proof-survives-handoff`, `real-check-unavailable`, `teammate-loosened-check`) yet costs 2–3x
  there ($0.48 and 23 turns on handoff). It hurts on `fake-check-and-decoy` (3/3 → 2/3).
- The check-the-check split gained +2/15, which is noise. Its win is **cost**: a read-only question
  pays 7 turns instead of 10, and no state. It did not improve quality.
- `check.py` (603 lines) re-implements mutation/HOLLOW logic that `mutate.py`, `challenge.py` and
  `verify.py` already have. Two copies of one engine will drift.

## Where the wasted turns go (from `actions.txt`)

1. **Answer-gate guessing.** `green-with-unverified` turns 10–15: the agent greps `verify.py` and
   `gates.py` to find out why `answer-check` said `MISSING`. `teammate-loosened-check` turns 6–8:
   it adds one `GAP` line per rejected try. The gate rejects without saying what would pass.
2. **Multi-command assess.** The Assess section is 3 commands; agents then add `baseline` and
   `run --strict`, so 4–5 helper calls answer one question.
3. **Re-orientation.** Every run spends 2–3 turns on `ls`/`cat`s that `report` could have printed.

Turns are the cost. Every design choice below removes turns, not lines.

## Design

### 1. One engine, shared by both skills
- Move the mutation, HOLLOW, NEVER LOADED/NEVER RAN and `--base` logic into one module
  (`scripts/engine.py`, stdlib-only). `verify.py run/challenge --assess` and `check.py` both call it.
- Each skill must stay installable on its own, so check-the-check carries a copy. A test makes
  that copy byte-identical to verify-loop's (`tests/test_engine_sync.py`). Drift fails CI;
  nobody has to remember to copy it.

### 2. Two front doors, chosen by the question
| Question | Skill | Calls |
|---|---|---|
| "Would this test, suite, gate or PR test catch a bug?" (read-only, no recipe) | check-the-check | `check.py` ×1 |
| "Is this claim or change proven?" (assess, keeps nothing) | verify-loop | `verify.py assess` ×1 |
| "Make it verified / repair / keep it proven" | verify-loop | `verify.py advance` loop |

- New `verify.py assess <repo> --json` = run + challenge --auto + report in one call, in a temp
  state dir. It replaces the three-command Assess section.
- `advance` already covers prove/repair; it keeps its decision stops.

### 3. The helper writes the answer, the agent fills in judgment
- `assess` and `report` print `ANSWER DRAFT:` with the `VERDICT:` line and every required `GAP`
  line already in place. It leaves marked slots only for what needs a model: the product-terms
  meaning of each survivor and the spec citation.
- `answer-check` lists **every** missing or unsupported line at once, with the exact text that
  would satisfy it. It never answers with a bare `MISSING`.
- Result: answer-check passes on the first or second try. Grepping the helper's source is never
  needed.

### 4. Orientation in the first output
- `assess`/`advance` begin with a short header: features, mapped files, last receipt per feature,
  frozen or not, and git changes since the baseline. This replaces the opening `ls`/`cat` turns.
- On a handoff, the second session reads that header. It doesn't need to re-run the proof unless
  inputs changed (`stale`).

### 5. SKILL.md stays a router (target ≤ 70 lines)
- The opening, the step table, Guards and the answer contract stay. The Assess section shrinks to
  one command.
- The Modes table points at references. Only rules that the evals show winning stay in the body
  (see `evals/SKILL_CUTS.md`). Everything else goes to a reference or is cut.

### 6. Cost is a gate, not a hope (mechanics, not advice)
- Each `evals/cases/*/expect.json` gets `max_turns` and `max_cost`. Set them at bare-arm mean
  ×1.5 where bare already passes, and ×3 where the skill is needed.
- `grade.py` fails a try over budget, the same as a missed finding. Also a failure: any Read/grep
  of the skill's own `scripts/` (proof the output was not self-explaining).
- Eval spend: a change re-runs only the cases whose skill/script it touches (map case → files in
  `expect.json`). The full 13×2×3 suite (~$12) runs per release only.

## Targets for the next release

| Metric | 1.18 | Target |
|---|---|---|
| verify-loop pass rate | 33/39 | ≥ 36/39, no "hurts" |
| verify-loop mean turns | 10 | ≤ 7 |
| verify-loop mean cost / bare | 2.1x | ≤ 1.5x |
| `proof-survives-handoff` turns | 23 | ≤ 10 |
| answer-check rejections per try | up to 3 | ≤ 1 |
| Helper-source reads in skill runs | yes | 0 |

## Order of work (each slice: failing test first, then eval subset)

1. `answer-check` lists all misses with the fix text, plus a test. Cheapest slice, biggest
   turn waste.
2. `ANSWER DRAFT:` in `report`/`assess`.
3. `verify.py assess` single call; shrink SKILL.md's Assess section.
4. Extract `engine.py`; point `check.py` at it; sync test.
5. Orientation header; re-run `proof-survives-handoff` and `teammate-loosened-check`.
6. Budget fields + helper-source-read failure in `grade.py`; set budgets from 1.18 data.
7. Re-run `fake-check-and-decoy` (1ef01c4's "still passed" wording should fix the miss); full suite
   at release.
