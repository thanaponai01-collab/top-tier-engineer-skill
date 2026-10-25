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

- **When:** 2026-10-26-0207
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 3
- **Plugin version:** 1.33.0
- **Cost of this run:** $3.58
- **User CLAUDE.md characters seen by both arms:** 0 (0 = isolated; anything else reaches both sides)
- **Claude Code:** 2.1.310 (Claude Code)
- **Raw evidence:** `evals/results/2026-10-26-perf-optimize-baseline/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `perf-optimize-benchmark-validity` | `perf-optimize` | are these measured gains valid? | 3 of 3 | 1 of 1 | no difference — the agent already does this |
| `perf-optimize-gain-outlives-session` | `perf-optimize` | does the speed-up outlive the session? One session makes the nightly report fast; a teammate then, unmentioned, rewrites dedupe to count retried rows and makes it quadratic again (3.5 s today, minutes at 10x, every figure unchanged); a fresh session, no skill in either arm, is asked only to add an average-order line and say whether it is ready for tonight's tenfold export | 3 of 3 | 1 of 1 | no difference — the agent already does this |
| `perf-optimize-general` | `perf-optimize` | the nightly report takes about 1.4 s on last night's export and the export is about to grow tenfold; make it fast without changing a figure it prints | 3 of 3 | 1 of 1 | no difference — the agent already does this |
| `perf-optimize-n-plus-one-and-decoy` | `perf-optimize` | what happens to this dashboard as the customer count grows? | 3 of 3 | 1 of 1 | no difference — the agent already does this |

**Cost per try** (mean $ · wall seconds · turns · tries that ran scripts/verify.py):

| Case | Without skills | With skills |
|---|---|---|
| `perf-optimize-benchmark-validity` | $0.12 · 39s · 4 turns · verify.py 0/3 | $0.15 · 40s · 5 turns · verify.py 0/1 |
| `perf-optimize-gain-outlives-session` | $0.42 · 564s · 18 turns · verify.py 0/3 | $0.47 · 1169s · 17 turns · verify.py 0/1 |
| `perf-optimize-general` | $0.16 · 314s · 7 turns · verify.py 0/3 | $0.28 · 738s · 9 turns · verify.py 0/1 |
| `perf-optimize-n-plus-one-and-decoy` | $0.12 · 37s · 4 turns · verify.py 0/3 | $0.23 · 62s · 6 turns · verify.py 0/1 |
| **all** | $0.20 · 238s · 8 turns · verify.py 0/12 | $0.28 · 502s · 9 turns · verify.py 0/4 |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
7 of 16 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 4 tries.
Counts Skill calls and direct Reads matched to actual staged files; these are tool requests,
not proof of successful reading or procedure compliance. Unmatched SKILL.md requests remain
in result.json as candidates; missing staging evidence makes historical loading unmeasured.

## Why tries failed

None failed.

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever the skill or the model changes.
