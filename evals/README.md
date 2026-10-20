# Evals: does verify-loop make an agent better, and at what cost?

The scripts under `plugin/skills/verify-loop/scripts/` have unit tests. The skill's instructions do
not, so this folder tests them the only honest way. It hands a real agent a rigged codebase, once
with the skill and once without. It counts how often each side gets the case right and what each
try cost.

Each case under `cases/<name>/` holds:

| file | what it is |
|---|---|
| `prompt.md` | the words for the **with** arm (names the skill) |
| `prompt-plain.md` | the same task for the **without** arm, with no skill named |
| `fixture/` | the codebase the agent works in, with the defect already planted. It is copied to a temp folder, so the agent never sees the rest of the case |
| `expect.json` | what a correct report must state (`planted`), the wrong answers it must not give (`traps`), and for some cases what the finished folder must look like (`workdir`, `actions`) |
| `reference/` | `good.md`, `good-alt.md` and `bad.md`, which prove the grader passes a right report and fails a wrong one (`tests/test_evals.py`) |

## The nine cases

| case | planted | trap |
|---|---|---|
| `verify-loop-check-cannot-fail` | a test that loops over a missing data file, so it runs zero cases and prints OK | reading "1 check passes" as "refunds verified" |
| `verify-loop-make-it-verified` | the same vacuous test, but the ask is "get it verified". Graded on the finished folder | a check that still can't fail, or proof that is only claimed |
| `verify-loop-green-with-unverified` | a feature with no VERIFY.md section | reading green as "every feature verified" |
| `verify-loop-check-is-wrong` | a stale test that makes the suite red over correct code | editing the test or the code to get green |
| `verify-loop-fake-check-and-decoy` | a test that recomputes its expected value and never calls the code | a neighbouring trivial test that really does call it |
| `verify-loop-challenge-survivor` | a mutation the check does not notice | changing the product, the check or the mutation |
| `verify-loop-change-shared-caller` | a shared value changed by `change.diff` that breaks an adjacent caller | checking only the feature the diff names |
| `verify-loop-ci-fresh-proof` | fresh CI proof that rejects a weak check | trusting the copied local green state |
| `verify-loop-healthy-check` (held out) | a healthy check backed by the implementation | rewriting correct expectations |

## Running it

Every agent run costs real money. Dry-run first:

```bash
python evals/run.py --dry-run
```

One case, one try per arm (about $1–3):

```bash
python evals/run.py --cases verify-loop-healthy-check --repeats 1
```

The full batch is 9 cases × 2 arms × 3 tries = 54 runs, capped at $5 each:

```bash
python evals/run.py --repeats 3 --jobs 4
```

Each batch goes to `results/<stamp>/`. For every try that folder keeps:

- `report.md`: what the agent wrote
- `actions.txt`: one line per tool call
- `grade.txt`: the judge's verdict, the phrase grader's verdict and the action checks
- `result.json`: pass/fail, `cost_usd`, `seconds`, `api_seconds`, `turns`, and `helper_calls` (the
  `scripts/verify.py` subcommands the agent ran; empty means it never used the helper)
- `transcript.jsonl`: the raw stream. It stays local through `.gitignore`

`results/<stamp>/RESULTS.md` is the scorecard: pass counts with and without the skill, then mean
cost, seconds, turns and helper use per side.

Re-grade a saved batch without running any agents: `python evals/run.py --rescore evals/results/<stamp>`.
`python evals/verify_trust.py evals/results/<stamp>/summary.json` checks a batch against the bar in
`verify-trust.json`: 5 tries per case, a 95% pass rate and no tripped traps.

Reports are graded on meaning by `judge.py`, a separate Sonnet call that is never told which arm
wrote the report. Every finding it credits must quote the report, and an invented quote does not
count. Pass `--no-judge` to use only the free phrase grader in `grade.py`.

## Isolation

Each child agent gets:

- `--setting-sources project,local`, so the person's own settings, installed plugins and user skills
  stay out
- `--strict-mcp-config`, so the account's claude.ai connectors (Drive, Calendar, Docs) are not
  loaded
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` and `--no-session-persistence`
- a clean environment, an empty `gh` config and a fresh temp folder

**Known gap:** `~/.claude/CLAUDE.md` still loads despite `--setting-sources` (probed 2026-10-11). The
runner records its length in `meta.json` and in the scorecard, and warns when it is not empty.
Built-in skills that ship with Claude Code, such as `verify`, load in both arms.
