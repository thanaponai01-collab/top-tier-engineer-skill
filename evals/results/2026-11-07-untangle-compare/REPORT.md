# untangle (ours, 1.38.0 draft) vs caldoai `untangle-codebase` vs plain Opus, on Transcriber_v2

Date 2026-11-07. Model `claude-opus-5-5` in every arm. Repo: Transcriber_v2 rewound to `b3922e1`, with the
12 later commits removed. Each arm got a fresh copy.

**Short answer.** No arm made the three replay probes cheaper or more reliable than the original repo.
Every probe difference is within noise (n = 2 to 4 per cell). The arms differ in what the untangle
itself did:

- Ours was the cheapest ($1.11 and $1.74) and the smallest (3 files).
- Ours was the only arm to classify every red test correctly, and it named the D4 bug with `file:line`
  in 2 of 2 runs.
- But ours spent its one move on code the next 12 commits never touched. It skipped the two files that
  took 7 of those 12 commits, though its own helper ranked both of them.
- caldoai cost 2 to 3 times as much, and changed 38 and 58 files.
- caldoai never followed its own "list every problem first" step, and it misread the red tests.
- caldoai, plain Opus and our draft were all behavior-safe on the suite.

## Scoreboard

### The untangle run

Costs are the true cost: the **last** `result` event's `total_cost_usd`, which is cumulative (see the
harness bug below).

| arm | run | cost | wall | files changed (excl. `.untangle/`) | pytest after (base 1141 pass / 10 fail) | node after (base 731/731) |
|---|---|---|---|---|---|---|
| plain | U1 | $1.97 | 492 s | 22 | 1142 / 10 (+1 new guard test) | 731/731 |
| plain | U2 | $1.54 | 626 s | 23 | 1144 / 9 (new guard test; fixed the stale fake) | 731/731 |
| **ours** | O1 | **$1.74** | 794 s | **3** | 1141 / 10, same reds | 731/731 |
| **ours** | O2 | **$1.11** | 643 s | **3** | 1141 / 10, same reds | 731/731 |
| caldoai | C1 | $4.59 | 1265 s | 58 | 1142 / 10, same reds (+1 guard test) | **730/730** (deleted 1 test) |
| caldoai | C2 | $3.05 | 675 s | 38 | 1141 / 10, same reds | 731/731 |

- No arm turned a green test red.
- C1 deleted `tests/cutdeck_progress_text.test.cjs`'s CEP-global test, along with the `window.CutDeck*`
  globals it checked. Nothing in the repo reads those globals (`grep` in `x/`), so this looks dead,
  but it is the only arm whose test count went down.

### Replay probes

A fresh agent got the bug report on the arm's committed tree. It was graded by overwriting the test
files with their versions at the real fix commit, then running the probe's command.

| arm | D1 nativeCut read-back | D3 sync_plan | D4 silent split_cues | all | mean cost / probe |
|---|---|---|---|---|---|
| plain, original repo | 1/2, $0.80 | 2/2, $0.54 | 2/2, $0.68 | 5/6 | $0.67 |
| plain, untangled (U1, U2 × a/b) | 3/4, $0.85 | 3/4, $0.99 | 4/4, $0.75 | 10/12 | $0.87 |
| **ours** (O1, O2 × a/b) | 3/4, $0.94 | 4/4, $0.63 | 4/4, $0.81 | 11/12 | $0.79 |
| caldoai (C1, C2 × a/b) | 2/4, $0.81 | 4/4, $0.58 | 4/4, $0.81 | 10/12 | $0.73 |

- **Noise.** D1 is the only probe anyone fails. Its hidden test checks exact error wording
  (`missing after 3 fresh reads`, `does not match the plan .*first: missing`), and every failure,
  `orig` included, was a fix with different wording. C1-D1 failed both tries, but O2-D1-b failed the
  same way on a tree whose untangle never touched `nativeCut.js`. Nothing here separates the arms.
- **Time to the fault.** D4 agents took the same 13 to 26 tool calls in every arm before they first
  opened `split.py`:

  | arm | calls before `split.py` |
  |---|---|
  | orig | 13, 13 |
  | ours | 14, 16, 14, 26 |
  | caldoai | 15, 19, 14, 22 |
  | plain-untangled | 15, 22, 14, 14 |

  D1 and D3 agents opened the fix file at call 1 or 2 everywhere. The untangles moved nothing a probe
  needed, so no arm could have helped here.
- **The probes don't cover what we changed.** Our target was the align-panel wiring. None of the 12
  real later commits touches `main.js`, `align.js` or `alignPanel.js`, so this probe set cannot show
  whether that move pays off.

**Spend.** $28.79 in this session: 4 untangles for $10.49 and 24 probes for $18.30. The plain arms
were reused, not rerun. Tries: 1 per untangled repo first, then a second try (`-b`) once the
cumulative-cost bug showed the real spend. That gives 2 untangle runs × 2 probe tries per arm, the
same shape as the plain arm.

## Per-arm trace reconstruction

Method: the `reverse-engineer-anything` skill's own routing says a source repo or plain-text log is
not a REA target ("for ordinary analysis of a complete source repository, use normal repository
tools"), so no REA tools ran. I applied its staged method instead:

- a question checklist (read, scope, move, proof, spend);
- one evidence ledger per run (`harness/trace.py` → `data/trace-*.txt`);
- every claim kept apart as observed, inferred or unknown.

Each claim below cites the call index in that run's timeline.

### Plain Opus (U1, U2), reused from the earlier trace

- **Read.** Shell only (`sed -n`, `grep`, `cat`): U1 made 0 Read calls, U2 made 2. It first read
  `ls-files` and line counts, then the audit report, `TODO_LEDGER` and `VERIFY.md` (U1 calls 0 to 3).
- **Scope.** Static only. `git log` appeared once as `--oneline | head -5` (U1#0) and once as
  `| wc -l` (U2#0). U2 ran one `git log -L` to date a bug (U2#17).
  - It looked for duplicate `def` names (U1#6, U2#4) and for imports from `transcribe` into `cutdeck`
    (U1#16, U2#22).
  - Both found the `transcribe → cutdeck.words` back-edge and duplicated silence helpers.
  - U2 also found a doc (`docs/architecture-review-20260910.html`) that already recommended the move.
- **Moved.**
  - `git mv cutdeck/words.py transcribe/words.py`, with its importers repointed.
  - The silence-helper copies in `rules.py` merged into `segment.py`.
  - `cmProject.js` stopped keeping its own copies of `randomUuid` and `isSide`.
  - U2 also fixed the stale `fake_split` test.
- **Proof.**
  - Both baselined pytest and node first.
  - Both wrote an import-direction test and saw it fail on the old code: U1 with `git stash` (U1#42),
    U2 by restoring the old import (U2#28).
  - Both reran both suites at the end.
- **Spend.** U1 lost turns to a pytest run it backgrounded, then polled and killed (U1#30 to 36).
- **D4 bug.** U2 named the D4 bug (`split.py:177/415/419`) in its answer, from the red test. U1 did
  not. Neither wrote it into the repo.

### Ours (O1, O2)

- **Read.** The skill, then the helper's ranking (O1#1). The ranking:

  | file | commits | fixes |
  |---|---|---|
  | `main.js` | 58 | 15 |
  | `faster_whisper.py` | 31 | 16 |
  | `align.js` | 29 | 11 |
  | `adjustmentLayer.js` | 22 | 11 |
  | `store.py` | – | – |
  | `spike18_split_probe/main.js` | – | – |
  | `nativeCut.js` | – | – |
  | `panel.js` | – | – |

  It also listed 5 pairs. Then the agent read `git show`, `git log -p` and `git log -L` on the commits
  the ranking cited (O1#8 to 21, O2#5 to 15).
- **Scope.** Fully history-driven: 11 and 12 history or helper commands, against 1 to 3 in every
  other arm.
  - Both runs found the same cost independently: each new align intent had to be hand-copied into
    `main.js`'s 12-line `alignPanel.bind` list.
  - `a662187` is the fix for a handler someone forgot to copy ("Text 1/2/All switcher dead live").
  - Both runs skipped the other 6 hotspots, mostly with "fixes local to one file, no cross-file repeat".
  - See `data/O1-untangle-notes.md` and `data/O2-untangle-notes.md`.
- **Moved.**
  - `features/align.js` now owns one `intents` object, and `main.js` binds it whole.
  - O1 also folded the tab-poll rule that was written twice into one `followTab()`.
  - The `main.js` test that pattern-matched the source text became one that builds the feature and
    checks every intent the panel raises.
  - In total 3 files, about 45 lines.
- **Proof.**
  - The gate's guard (`node --test tests/cutdeck_align_panel.test.cjs`) passes now, fails on a
    worktree of the base (gate), and failed when the agent renamed a handler by hand (O1#48).
  - The full suites were rerun by the gate: `UNTANGLE-GATE: done`.
  - Every red got `env`, `stale` or `bug`. In both runs the D4 bug was written as `bug:
    transcribe/cues/split.py:177 ... faster_whisper.py:771`, and the stale fake was dated to
    `307671f`.
- **Spend.**
  - In O1, 33 of 52 calls came before the first edit: history reading plus slot filling. O2 made
    every edit through the shell, so there is no clean split.
  - O1 lost its first baseline: it passed `node --test tests/` (exit 1, "1 test") and pytest with an
    unknown `--timeout=0` (exit 4, no count), and the gate **saved that as the baseline** (O1#3). The
    agent ran `rm -rf .untangle` to start again (O1#4).
  - Both runs wrote 8 identical `env: uharfbuzz` lines, one per parametrized test.
  - O2 wrote a `move` line for `alignPanel.js` that says "file unchanged", because the pair target made
    that file a target. The gate accepted it.

### caldoai `untangle-codebase` (C1, C2)

The skill has no scripts or references, only `SKILL.md` (`data/caldoai-untangle-codebase-SKILL.md`).

- **Read.**
  - Both built an import graph by script (C1#5, C2#0), then sent read-only survey subagents out
    (C1: 2, C2: 3).
  - Main-thread reading happened through `sed -n` and `grep`, as in plain.
- **Scope.** Static.
  - C1 ran a churn count (`git log --name-only | uniq -c`) at call 30, after its first moves had already
    landed (C1#19 to 25), and did not act on it. C2 ran one churn count at call 0 and never referred to
    it again.
  - Neither looked at a single fix commit.
  - Targets came from the import graph and the subagents' duplicate lists.
- **Steps skipped.** The skill's "2. List every problem. Don't change anything yet" and its decision
  log were never produced.
  - There are 0 problem lists and 0 log files.
  - "Special case" appears 0 times in either transcript.
  - Edits began at C1#19 and C2's first move, while the survey subagents were still running.
  - The "1. Ask" step was answered by the agent ("chose neither" Comments nor Tests). The prompt told
    every skill arm it was unattended.
- **Moved.**
  - The `words.py` move, as in plain (C1 to `transcribe/thai/words.py`).
  - C1 also: one owner for the Thai character range (5 copies) and for boundary tolerance (4 copies),
    the cut-label constants, a shared `buildSeedProject` for `alProject.js`/`cmProject.js`,
    re-export cleanups, about 20 unused JS exports removed, 8 unused Python functions deleted, and
    `window.CutDeck*` globals removed.
  - C2 also: silence helpers, protocol constants owned by `helper.py`, two functions moved to
    `sequence_model.py`, 17 unused exports removed, re-export pass-throughs removed.
- **Proof.**
  - Baseline and after runs of both suites, with failures diffed by name (C1#74).
  - C1 checked its boundary test against stashed code (C1#88) and compared old and new
    `alProject`/`cmProject` output byte for byte (C1#51 to 52).
  - C2 had a reviewer subagent check the diff, which found nothing.
  - C2's last edit (`biasindex.py`) landed after its final full run. It said so.
- **Red tests misread.**
  - C1 said 7 failures were `uharfbuzz` and 3 were "two cue-splitter tests and one faster_whisper".
    The real split is 8 and 2.
  - C2 blamed "Python 3.13 instead of 3.11, and fonts".
  - Neither named the D4 bug, though a red test points straight at it.
- **Spend.** 126 and 97 tool calls (24 and 32 of them by subagents), against 44 and 55 for plain, plus
  subagent tokens (Sonnet: $0.33 and $0.56). C1
  ended by saying it stopped before the skill's "repeat until nothing is left" loop finished.

### Contrast: our gate's demands vs caldoai's steps

| idea | caldoai | ours | what the traces show |
|---|---|---|---|
| Scope from git history | a tip ("Use Git as evidence") | ranked hotspots and pairs, each needs `target`/`skip` | caldoai: 1 churn count per run, unused. Ours: 11 or 12 history commands per run, and the target came from fix commits |
| Baseline on the committed tree | not asked | stage 1 | caldoai and plain did it anyway. Ours accepted a broken baseline (O1#3) |
| Classify reds | not asked | env/stale/bug with `file:line` | ours 2/2 correct with the D4 cause. caldoai 0/2 correct. plain 1/2 named the bug |
| Guard fails on base | not asked | stage 2, checked in a worktree | C1, U1 and U2 did this by hand for their boundary test. Only ours is forced to |
| Problem list before changing anything | step 2, prose | none | not followed in either caldoai run |
| Import graph / dependency direction | tip plus done-criterion | none | all 4 non-ours runs found and fixed the `transcribe → cutdeck` back-edge. Ours never saw it, because `cutdeck/words.py` is not a hotspot |
| Special-case census (`if` for one value, sleeps, swallowed errors) | step 2, prose | none | 0 mentions in caldoai runs |
| Dead code / unused exports | "Surplus" | none (latent-audit's job) | C1 and C2 deleted 25 to 30 symbols. The suite stayed the same |
| Subagent re-check loop | step 5, "until nothing is left" | none | 2 or 3 subagents per run, then stopped early because of budget |
| Optional comment or test pruning | step 1 asks | none | both declined |

## Ranked improvements to `plugin/skills/untangle`

Each one is tied to trace evidence and is a mechanical check, not advice.

1. **Don't let the busiest fix hotspots be waved off as "local to one file".**
   - *Evidence:* the 12 real later commits are 5 fixes to `nativeCut.js` and 2 to `faster_whisper.py`,
     with the rest elsewhere. Our helper ranked both files (#7 and #2). Both runs skipped both, with
     "fixes local to this file; no cross-file repeat" (notes files).
   - *Evidence:* our one target got 0 of the 12 later commits. So the ranking predicted where changes
     would land, and the skip rule threw that away.
   - *Change (`untangle.py`):* a hotspot whose fix commits make up at least half of its commits, or
     are at least 5, can't take a bare `skip`. Its `skip` must name a guard command (run by the gate,
     like a move's guard) that covers the repeated fix class, or the hotspot becomes a target.
   - *Change (SKILL.md, stage 1):* "repeated fixes in one file are a tangle inside the file".

2. **Refuse a baseline that ran nothing.**
   - *Evidence:* O1#3. `node --test tests/` exited 1 with "1 test", and pytest exited 4 with no count.
     The gate saved both as the baseline, with "0 red". The agent had to `rm -rf .untangle` (O1#4).
   - *Change:* in `take_baseline`, if any command parses to `ran in (None, 0)`, or pytest exits 4 or
     5, print `STAGE 1 OPEN: <cmd> ran no tests (rc N): fix the command` and **don't** write
     `state.json`. Add a test in `tests/test_untangle.py` with a bad pytest flag.

3. **Put a `bug` red where the next debugger looks, not only in `.untangle/notes.md`.**
   - *Evidence:* both of our runs named the D4 cause as `split.py:177`, and the notes were committed.
   - *Evidence:* 1 of 12 probe agents ever opened `.untangle/notes.md` (O1-D1, a D1 probe). The four
     D4 probes on our trees took 14, 16, 14 and 26 calls to reach `split.py`, the same as `orig` (13,
     13).
   - *Evidence:* the D4 agents did grep the tests for `unpack` (O2-D4 call 8).
   - *Change:* a `bug` line passes only once a comment containing `untangle: known bug` and the error
     text sits at the named `file:line` or at the failing test. The gate greps for it. The comment
     changes no behavior.

4. **One move per pair target, and a `move` on an unchanged file is an error.**
   - *Evidence:* the `alignPanel.js + main.js` pair made `alignPanel.js` a target. O1 had to write
     `not moved`. O2 wrote `move ...: file unchanged | guard: ...`, and the gate accepted it.
   - *Change:* a pair target adds a single `- move <a> + <b>: ...` slot. A `move` for a file outside
     `changed_since(base)` raises `STAGE 2 OPEN: move <t> names no change; say not moved`.

5. **Group reds that fail for the same reason.**
   - *Evidence:* O1 and O2 each wrote 8 identical `env: uharfbuzz` lines (parametrized
     `test_text_box`).
   - *Change:* `parse_run` keeps pytest's `FAILED x - <message>` text. Reds with the same message
     share one slot, `- red <file>::* (<message>): ...`.

6. **Add the dependency-direction check caldoai only describes, with volatility measured from history.**
   - *Evidence:* U1, U2, C1 and C2 (4/4 non-ours runs) each found `transcribe/` importing
     `cutdeck.words`, moved it, and added a boundary test red on base. Ours never saw it, because no
     ranked hotspot points there.
   - *Honest caveat:* no probe got faster from that move (D4's `split.py` imports `words` in every
     arm).
   - *Change:* the helper also lists import cycles between top-level packages, plus edges where a
     file imports one with at least 3 times its churn. Each needs `target`/`skip`, like a hotspot.
     This is caldoai's "nothing imports anything more volatile", made mechanical with our own churn
     counts.

7. **Rank out dead experiments and pure feature churn.**
   - *Evidence:* both runs spent a `skip` on `uxp/spike18_split_probe/main.js` ("throwaway live probe,
     last touched 2026-08-26") and on `store.py` ("single SQL owner by design").
   - *Change:* weight commits by recency, or drop files untouched in the last N commits.
     Score = churn + 2×fixes already favours fixes; consider ranking by fixes first.

8. **Keep what works, and say so in SKILL.md.**
   - History-scoped targets with cited commits, `bug` reds with `file:line`, and guards checked on a
     worktree of the base are the three things only our arm did every time.
   - caldoai's prose steps (problem list, special cases, decision log) were skipped 2 of 2 times, so
     copying them as prose would add nothing. That is the CLAUDE.md rule, "mechanics, not advice",
     confirmed again.

## Harness and eval findings, outside the skill

- **`evals/agent.py` `parse_stream` overstates cost when a run has more than one `result` event.**
  `total_cost_usd` is cumulative. C1's two results both say $4.587, and C2's three say $2.887, $2.887
  and $3.051. Summing them gave C1 $9.17, C2 $8.83 and plain U1 $2.95 instead of $1.97. Any earlier
  eval with background tasks may be affected. `harness/costs.py` takes the max. This is a fix outside
  this task's write scope.
- **The probe set can't score our kind of move.** None of the 12 real later commits touches the
  align wiring, so a fair eval of `untangle` needs a probe that lands on what each arm moved, or a
  longer replay window.
- **n is tiny.** 2 untangle runs per arm and 4 probe tries per (arm, probe), against 2 for `orig`.
  Every probe difference above is noise. The untangle-side differences are consistent in both runs
  of each arm: cost, file count, red classification, and use of history.

## Files

- `harness/cmp.py`: the arm runner, adapted from the parent's `txh.py`. It adds `plugin_dir`, an
  overwrite regrade and a node-aware suite.
- `harness/trace.py`, `harness/probes.py`, `harness/costs.py`: the trace ledger, the per-probe
  time-to-fault table and the true cost.
- `data/`:
  - `trace-*.txt`: call timelines.
  - `untangle-*.json`: each run's answer, diff file list and suite.
  - `O*-untangle-notes.md`: the gate notes.
  - `costs.json`, `probes.json`, `suite-*.json`.
  - `prompt-*.txt`: the exact prompts.
  - `caldoai-untangle-codebase-SKILL.md`: their skill as fetched on 2026-11-07.
- Local paths are redacted to `<scratch>` and `<home>`. The run repos and full `stream.jsonl` files
  stay in the session scratch folder, not in the repo.
- Prompt: the plain arm's `UNTANGLE_PROMPT`, plus, for skill arms only: "Use the <name> skill. … is at
  <path>. Read and follow that SKILL.md before starting. You are running unattended: nobody will
  answer questions, so make any choice the skill leaves to the user yourself." The last sentence was
  added because caldoai's step 1 asks the user a question.
