# Scorecard — does verify-loop make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-25-1822
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.30.0
- **Cost of this run:** $2.18
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/debug-protocol-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `debug-protocol-distant-cause` | `debug-protocol` | the total is wrong where it is printed; where does it actually go wrong? | 0 of 3 | 3 of 3 | **skill helps** |
| `debug-protocol-regression-proof` | `debug-protocol` | Is the fee's cause proven, fixed at its source, and held by a check that was seen rejecting the bug? | 0 of 3 | 0 of 3 | both fail — fix the skill or the case |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `debug-protocol-distant-cause` | $0.08 · 17s · 3 turns · verify.py 0/3 | $0.12 · 35s · 5 turns · verify.py 0/3 |
| `debug-protocol-regression-proof` | $0.13 · 39s · 6 turns · verify.py 0/3 | $0.39 · 85s · 15 turns · verify.py 3/3 |
| **all** | $0.11 · 28s · 4 turns · verify.py 0/6 | $0.26 · 60s · 10 turns · verify.py 3/6 |

**Did the agent open the skill it was asked to use?** 0 of 6 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

- `debug-protocol-distant-cause` **without**: missed: test_totals only uses whole-number amounts and never runs parse.py, so the suite cannot see it; did not do it: reproduced the failure before changing any code (changed the code first; ran it only afterwards); did not do it: left parse.py alone (changed: outside the files this run may change); did not do it: left test_parse.py alone (added: outside the files this run may change)
- `debug-protocol-distant-cause` **without**: missed: test_totals only uses whole-number amounts and never runs parse.py, so the suite cannot see it; did not do it: reproduced the failure before changing any code (changed the code first; ran it only afterwards); did not do it: left parse.py alone (changed: outside the files this run may change); did not do it: left test_parse.py alone (added: outside the files this run may change)
- `debug-protocol-distant-cause` **without**: did not do it: reproduced the failure before changing any code (changed the code first; ran it only afterwards); did not do it: left parse.py alone (changed: outside the files this run may change); did not do it: left test_parse.py alone (added: outside the files this run may change)
- `debug-protocol-regression-proof` **with**: did not do it: left .verify-state-cache/tree-9b386718ed52195c.json alone (added: outside the files this run may change)
- `debug-protocol-regression-proof` **with**: did not do it: left .verify-state-cache/results.json alone (added: outside the files this run may change); did not do it: left .verify-state-cache/surveys.json alone (added: outside the files this run may change); did not do it: left .verify-state-cache/tree-38c6ed179a20e21b.json alone (added: outside the files this run may change)
- `debug-protocol-regression-proof` **with**: did not do it: left .verify-state-cache/tree-2519d03b12aec28a.json alone (added: outside the files this run may change)
- `debug-protocol-regression-proof` **without**: did not do it: Retained state is strict green. (.verify-state.json is not there); did not do it: Checks passed. (.verify-state.json is not there); did not do it: Actual rejection evidence exists. (.verify-state.json is not there)
- `debug-protocol-regression-proof` **without**: did not do it: Retained state is strict green. (.verify-state.json is not there); did not do it: Checks passed. (.verify-state.json is not there); did not do it: Actual rejection evidence exists. (.verify-state.json is not there)
- `debug-protocol-regression-proof` **without**: did not do it: Retained state is strict green. (.verify-state.json is not there); did not do it: Checks passed. (.verify-state.json is not there); did not do it: Actual rejection evidence exists. (.verify-state.json is not there)

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
