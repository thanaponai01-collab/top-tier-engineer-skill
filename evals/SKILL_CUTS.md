# SKILL.md cuts (1.17.0): the evidence behind each one

SKILL.md went from 148 lines (1.16.0) to 99 (1.17.0), 88 of them below the frontmatter. A rule stays only if (a) the evals show the
skill arm beating the bare arm on the behavior it drives, or (b) `verify.py` enforces it and the
agent has to know about it to act on the helper's verdict. Anything else is cut, or moved to
`references/` when it is a lookup. No agent runs were paid for to make this table. It uses:

- the historical ledger, `git show ddcd651~1:evals/LEDGER.md` (bare arm → skill arm);
- the per-run `grade.txt`, `actions.txt` and `report.md` under `ddcd651~1:evals/results/`
  (`2026-09-29-1859`, `2026-10-05-*`, `verify-loop-rewrite*`, `p07-*`);
- `evals/results/2026-10-20-runner-proof/`;
- `CHANGELOG.md`, for rules added after an observed eval failure;
- the current helper run with `--assess` on each case fixture, to see which verdicts it prints
  today.

Those runs used older SKILL.md versions (top-tier-engineer 4.43–4.61). A result counts for a rule
when the same rule was in the skill then and the run's actions or report show it was acted on.

## What the runs show

| Case | Bare → skill | What decided it |
|---|---|---|
| `check-is-wrong` | 0/3 → 3/3 | All three bare runs edited `test_discount.py:11` to go green. All three skill runs stopped and asked a person, and **none of them called the helper**: the prose rule "a check you think is wrong is a finding, not an edit" did this alone. |
| `challenge-survivor` | 0/1 → 1/1 | Both arms found the survivor. The bare arm failed the workdir check only: no `challenge` receipt in `.verify-state.json`. The skill's value was the retained receipt. |
| `make-it-verified` | 0/1 → 1/1 | Both arms named the broken loader. The bare arm left no `fail-proof:` line, no `baseline` and no strict green, and its repaired test did not go red on the original bug. The skill's value was the prove → freeze → strict path. |
| `check-cannot-fail` | 0/3 → 1/3 | The winning skill run broke `refund.py` (`return "garbage"`) and ran the check (the "prove it fails" step). No bare run did. 1.15.0 made this mechanical: `run` now says `HOLLOW` and goes red on this fixture. |
| `fake-check-and-decoy` | 3/3 vs 3/3 | No difference. "Watches the real thing" adds nothing; `HOLLOW` covers the fixture's pattern. |
| `green-with-unverified` | 0/3 vs 0/3 | Both arms missed `the-checks-are-unproven` (no fail-proof). With a later SKILL.md (`verify-loop-rewrite-2`, skill arm only) 2/2 passed, and today `report` prints `GAP never seen red` for both features. `search.py` (a feature with no section) was found by every run in both arms, but **the helper cannot see it**: `report` says `0 unverified`. |
| `p07-running-artifact-identity` | 1/1 vs 1/1 | No difference. Across `p07-replay`/`p07-run2`/`p07-final` the skill arm missed `health-is-not-identity` as often as the bare arm. |
| `healthy-check` (2026-10-20) | 1/1 vs 1/1 | No difference, $0.13 → $0.20. The skill run did not use the helper. |
| `change-shared-caller`, `ci-fresh-proof` | never compared | Every solo run on either side passed. Unmeasured. |
| 4 structural cases | never run | See "Structural cases" below. |

Helper use: across the historical skill-arm runs, most action logs show zero or one `verify.py`
call, and the decisive behaviors above (`check-is-wrong`, the `check-cannot-fail` win) came
from prose or from manual mutation, not from the helper. CHANGELOG 1.16.0 records that one eval
agent skipped the helper because `run` wrote into the repo; `--assess` was the fix. So the slim
SKILL.md opens with the helper and gives `report` → `NEXT` as the one way through.

## Section by section

Result key: **helps** (the skill arm beat the bare arm on this behavior), **no diff**, **both
fail**, **unmeasured**. "Enforced" means `verify.py` turns the rule into a verdict.

| SKILL.md section / rule (1.16.0) | Eval cases | Result | Enforced by `verify.py` | Decision |
|---|---|---|---|---|
| Frontmatter `description` | all (triggering) | n/a | no | **keep** unchanged; it is what triggers the skill |
| Opening lines ("build the check before the work…"; "someone who did not watch can trust the claim") | none | unmeasured | no | **keep, rewritten** as the purpose plus the five things the helper does that a model can't |
| Quick path: `run` / `challenge --auto` / `report` with `--assess` | `healthy-check`; CHANGELOG 1.16.0 (agent skipped the helper because it wrote to the repo) | added to fix an observed failure | yes (`--assess`, `HOLLOW`, `SURVIVED`, `UNCOVERED`) | **keep** |
| "No VERIFY.md yet? Write the three lines" | `check-is-wrong` fixture has no VERIFY.md | unmeasured | `report` prints `unverified` with no recipe | **keep, one line** |
| **Done** definition | `make-it-verified` (workdir: fail-proof, baseline, strict green), `challenge-survivor` | helps | yes (`run --strict`, `status`, `UNCHALLENGED`) | **keep** |
| A good check 1 "Can fail" | `check-cannot-fail` (winning run did it), `make-it-verified` | helps | yes (fail-proof receipts, `SIGNAL IN PASS`, `HOLLOW`, `GAP never seen red`) | **keep as the `prove` step**, not as a principle |
| A good check 2 "Watches the real thing" | `fake-check-and-decoy` | no diff (3/3 vs 3/3) | yes, `HOLLOW` for Python `test:` checks | **cut**; `HOLLOW` stays named in the quick path |
| A good check 3 "Expects what the spec says" | `healthy-check`, `fake-check-and-decoy` | no diff | `oracle:` + `CHECK CHANGED` once frozen | **cut**; already in `references/answer.md` ("never the code") |
| A good check 4 "Fails specifically" | none | unmeasured | no | **cut** (advice) |
| A good check 5 "One cheap command" | none | unmeasured | no | **cut** (advice) |
| "Hollow check is broken machinery; `run` flags `HOLLOW`" | `check-cannot-fail`, `make-it-verified` | helps (leans) | yes | **keep** as the `HOLLOW` verdict |
| Loop 1 "Name the claim observably" | none | unmeasured | no | **cut**; duplicated in `references/answer.md` (what the caller passes) |
| Loop 2 Ladder of check strength (lint < unit < … formal) | none | unmeasured | no | **cut** (advice a frontier model already follows); `references/project-recipe.md` covers real-run checks |
| Loop 3 Record in VERIFY.md (`oracle:`, literal `fail-signal:`, `init`) | `challenge-survivor` (`challenge` refuses without a signal) | helps (indirect) | yes (`NEXT … [map]`, `challenge` needs a signal) | **keep** as the `map` row |
| Loop 4 Prove it fails, `fail-proof:`, "prose is not a receipt", `require: challenge` | `make-it-verified`, `check-cannot-fail`, `inherited-claim` (structural) | helps | yes (receipts, `NEXT … [prove]`, `UNCHALLENGED`) | **keep** as the `prove` and `challenge` rows |
| Loop 5 Freeze with `baseline` | `make-it-verified` (workdir) | helps | yes (`CHECK CHANGED`) | **keep** as the `freeze` row |
| Loop 6 `NEWLY RED` / `SAME FAILURE x2` / `BUDGET` | none | unmeasured | yes, helper verdicts | **keep, one line**: the agent must know what each verdict asks of it |
| Loop 7 A check you think is wrong is a finding; `--reviewed-by` | `check-is-wrong` | **helps 0/3 → 3/3, by prose alone** | yes after `baseline` (`CHECK CHANGED`, `BASELINE REFUSED`) | **keep, prominent** |
| Loop 8 Finish `run --strict && status`; `tests --strict` | `make-it-verified` | helps | yes | **keep** in Done; `tests --strict` is in `references/verify-change.md` already, so cut here |
| "Who does the work is the helper's call" (`SWARM:` solo/split/judge) | none | unmeasured | yes (`report` prints `SWARM:`; `swarm --claim` refuses a freezer as judge) | **keep, compressed**: the agent must act on `SWARM:` |
| Before done: changed behavior / adjacent caller with no check | `green-with-unverified` (`search.py`), `change-shared-caller` | found by both arms; **helper blind** | no: `report` prints `0 unverified` for a feature with no section | **keep, and flag: needs a mechanism** (see below) |
| Before done: a check never seen red | `green-with-unverified` | **both fail** (0/3 vs 0/3) in 2026-09-29 | yes now: `GAP never seen red` | **keep** as "every `GAP` line goes in the answer" |
| Before done: deleted, skipped or loosened test; hardcoded output | `teammate-loosened-check` (structural), `fake-check-and-decoy` | unmeasured / no diff | partly: `CHECK CHANGED` after a freeze, `review` for removed/skipped/fewer-assert tests, `challenge --auto` for a loosened assertion | **keep** in the guards |
| Before done: stale process or build answering (artifact identity) | `p07-running-artifact-identity` | no diff (1/1 vs 1/1; replays equal) | `## Run` identity checks | **cut**; lives in `VERIFY_FORMAT.md#run` and `references/project-recipe.md` |
| "An assessment reports; it edits product code only when a fix was asked for" | `healthy-check`, `challenge-survivor` | no diff | no | **cut**; `references/answer.md` defines `assess` mode |
| Fooled-checker intro ("a capable agent can pass a weak check…") | none | unmeasured | no | **cut** (advice); the guards below stay |
| Guard: separate judge from worker, `require: independent` | none | unmeasured | yes (`NOT INDEPENDENT`) | **keep, one line** |
| Guard: freeze before you build | `make-it-verified` | helps | yes | **keep** (folded into `freeze`) |
| Guard: sealed state, CI as the guard nobody in the loop can reach | `ci-fresh-proof` | unmeasured | yes (`tampered`, `ci`) | **keep, one line**; detail in `references/ci.md` |
| The answer (claim, scope, mode; `report`, `--json`) | all graded reports | n/a | yes (`report`) | **keep** |
| Modes table | n/a (lookup) | n/a | no | **keep** |
| Other helper commands line | none | unmeasured | n/a | **cut to one pointer** at `references/helpers.md`; keep where state lives |
| Closing *Test:* line | none | unmeasured | duplicates Done | **cut** |

## Added, from the structural cases

The four structural cases have not run. These lines keep them covered, each tied to a verdict
the helper already prints on that fixture (checked with `--assess`):

| Case | Helper says today | SKILL.md line that covers it |
|---|---|---|
| `real-check-unavailable` | `GAP failing check: … test_ledger.py`, `GAP blind spot: … ledgerctl`; `triage` says `HARNESS-GAP` | guard: never skip, mock, stub or drop a check to get green; a check that cannot run here stays red and is reported as blocked. `references/triage.md` gains the missing-tool case. |
| `inherited-claim` | `GAP never seen red: Refunds`, `REJECTED none observed` | guard: a note, handoff or commit message saying a check went red is a claim; only a receipt counts. |
| `teammate-loosened-check` | `GAP never seen red` only; no verdict for the `delta=2` loosening | guard: a loosened check is a finding; `review --base` / `challenge --auto` find it. **Flag:** no helper verdict names a loosened assertion before a baseline exists. |
| `proof-survives-handoff` | `NEXT … [map]` / `[prove]` / `[freeze]` | the `report` → `NEXT` loop itself: the next session reads receipts instead of re-deriving them. |

## Needs a mechanism, not more prose

- **A feature with no section is invisible to `report`.** `green-with-unverified` plants
  `search.py`; `report` prints `0 unverified` and no `GAP`. Every run found it by reading the
  folder, so the rule stays in SKILL.md, but the fix is a helper verdict: `report` listing
  product files no feature's checks or `path:` reach as `GAP unmapped: <file>` (what `review`
  already does for a diff as `UNMAPPED`).
- **A loosened assertion before any baseline.** `teammate-loosened-check` has no `baseline`, so
  `CHECK CHANGED` cannot fire; only `review --base` against the commit before the loosening, or
  a `challenge --auto` survivor, shows it.
- **`report` does not say a red is a missing tool.** On `real-check-unavailable`, `triage`
  already says `HARNESS-GAP … FileNotFoundError … Do NOT modify product logic`, but `report`
  only says `GAP failing check` and `NEXT [map]`. An agent that follows `NEXT` alone never sees
  the triage. `report` could carry the triage class on each failing-check gap.
