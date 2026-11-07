# Sonnet replay probes on the untangled Transcriber trees: results

Date 2026-11-07. Probe agent `claude-sonnet-5-5`, 2 tries per (tree, probe), 6 probes, 7 trees = 84
runs. Setup in `README.md`; per-cell table in `data/table.md`; rows in `data/probes.json`.

**Short answer.** Sonnet doesn't separate the arms either. Every untangled tree is within noise of
the original on pass rate, damage and effort, and no tree caused damage in any of the 84 runs. The
eval itself works. The reason it can't show a gain is that **none of the six probes lands in code
any arm moved**, and every probe agent reached the fix file by call 1 or 2.

## Totals

| arm | trees | passed | mean cost / run | mean calls | mean files read | damage runs |
|---|---|---|---|---|---|---|
| orig | x | 11/12 | $0.284 | 14.9 | 5.6 | 0 |
| plain Opus untangle | U1, U2 | 20/24 | $0.236 | 13.8 | 4.2 | 0 |
| ours (1.38.0 draft) | O1, O2 | 20/24 | $0.265 | 14.6 | 4.9 | 0 |
| caldoai | C1, C2 | 22/24 | $0.254 | 14.5 | 4.5 | 0 |

- The untangled trees look 7-17% cheaper per run than `orig`. But `orig` has n = 12 and the spread
  within a cell is about as big (D3 orig: $0.21 and $0.45), so this is not a finding.
- Calls before first touching the real fix file: 1-2 for every probe except D4 (4-7) in every arm. The
  bug reports name the area, so there is no search for structure to shorten.

## Why no arm could win here

| probe | fix file | moved by any arm? |
|---|---|---|
| D1, P6 | `uxp/cutdeck/timeline/nativeCut.js` | no. Ranked as a fix-heavy hotspot by our helper, skipped by both 1.38.0 runs |
| P5 | `transcribe/engines/faster_whisper.py` | no. Ranked #2, skipped by both 1.38.0 runs |
| D3 | `cutdeck/sync_plan.py` | no |
| D4 | `transcribe/cues/split.py` | no (`words.py` moved next to it in U/C arms) |
| P7 | `uxp/cutdeck/timeline/nativeSync.js` | no |

The one arm that would act on these files is untangle **1.41.0**. Its fix-heavy rule refuses a bare
`skip` on exactly `nativeCut.js` and `faster_whisper.py`, which take 3 of the 6 probes. That arm
hasn't been run.

## Harness fixes found by the run (and applied)

- **D4 prompt** said "crashes inside faster_whisper.transcribe". Sonnet read that as the library,
  patched our engine around the library's VAD, and never opened `split.py` (smoke run discarded).
  Now it names the engine file and the exact `ValueError`, as a real traceback would.
- **P7 grader vs prompt.** The real fix keeps the refusal text "already a synced copy", and its test
  checks that text. The first prompt didn't say so: 0/26 runs passed, all on that one assertion. The
  prompt now says to keep the error text, and P7 was rerun on every tree: 14/14. The 26 v1 runs are
  in the scratch `discarded-P7-v1/` folder and are excluded from the tables.
- Failed runs now keep their tree, so a grader change can be applied without rerunning the agent.

## Failures left (11 of 84)

- D3 (5 runs, spread across arms): the second hidden test, "does not stop later pieces", fails. A
  partial fix: the agent stopped refusing the piece, but the next pieces still didn't get tried.
- P6 (4), P5 (2): the hidden test fails on the agent's fix. These look like real misses.
- D1 (2: C1, O2): the retry went into `uxp/cutdeck/host/sequenceRead.js`, and the hidden test's fake
  host doesn't reach it. This may be a valid fix the grader can't see, the same as in the Opus
  compare run.

## Spend

$21.53 for the 84 counted runs, plus about $6.4 discarded (P7 v1 and the first D4 smoke), so about
$28 in total.

## Untangle 1.41.0 arm (N1, N2)

Two fresh Opus untangles of the cutoff tree with the plugin at 1.41.0 (`harness/untangle_arm.py`, same
prompt as the compare run). Both reached `UNTANGLE-GATE: done`.

| run | cost | calls | what it moved | nativeCut.js | faster_whisper.py |
|---|---|---|---|---|---|
| N1 | $1.21 | 32 | align intents (the same move as 1.38.0) | skip + guard (existing test file) | skip + guard |
| N2 | $1.10 | 28 | one tail-redecode path in faster_whisper.py | skip + guard | **target**: 3 copies of shift-and-merge into `_splice_tail` |

Both put `untangle: known bug:` comments at `split.py:177` (and :415 in N2), the D4 fix site.

### Sonnet probes on the 1.41.0 trees

| arm | passed | cost / run | tokens / run | calls | files read | damage runs |
|---|---|---|---|---|---|---|
| orig | 11/12 | $0.284 | 575k | 14.9 | 5.6 | 0 |
| plain | 20/24 | $0.236 | 484k | 13.8 | 4.2 | 0 |
| ours 1.38 | 20/24 | $0.265 | 537k | 14.6 | 4.9 | 0 |
| caldoai | 22/24 | $0.254 | 530k | 14.5 | 4.5 | 0 |
| **ours 1.41** | **22/24** | **$0.226** | **436k** | **12.8** | **4.0** | 0 |

| arm | D1 | D3 | D4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|
| orig | 2/2 $0.29 | 1/2 $0.33 | 2/2 $0.19 | 2/2 $0.31 | 2/2 $0.37 | 2/2 $0.22 |
| plain | 4/4 $0.22 | 3/4 $0.27 | 4/4 $0.12 | 3/4 $0.30 | 2/4 $0.31 | 4/4 $0.19 |
| ours 1.38 | 3/4 $0.23 | 2/4 $0.31 | 4/4 $0.19 | 3/4 $0.32 | 4/4 $0.34 | 4/4 $0.21 |
| caldoai | 3/4 $0.26 | 4/4 $0.21 | 4/4 $0.15 | 4/4 $0.40 | 3/4 $0.30 | 4/4 $0.22 |
| ours 1.41 | 4/4 $0.24 | 4/4 $0.25 | 4/4 $0.14 | 2/4 $0.21 | 4/4 $0.31 | 4/4 $0.21 |

**Read: still a tie.**
- 1.41.0 is the cheapest arm and the only one with both D1 and D3 at 4/4. But D3's fix file
  (`sync_plan.py`) is untouched in every arm, and D3 still ranges from 1/2 to 4/4 across arms. That
  is the size of the noise, and it covers every difference in the table.
- D4 (the known-bug comment sits at the fix site) didn't get faster. Calls before opening `split.py`
  were 3-5 on 1.41.0 and 3-11 elsewhere, because the reworded prompt already names the engine file.
- **P5 0/2 on N2, the one tree that restructured P5's area.** Both runs found the right function
  (`_batch_recover_tails`, now built on N2's `_splice_tail`). Both replaced seek grouping with
  assigning each word by its timestamp, instead of fixing the seek key. The hidden test calls
  `_group_segments_by_window` directly, so it fails. It's a fix the grader can't see, not a missed
  bug. The real fix still applies cleanly on N2's tree.

### Findings about 1.41.0 itself

- **The fix-heavy rule is met by naming an existing test.** Both runs skipped `nativeCut.js` with
  `guard: node --test tests/cutdeck_native_cut.test.cjs`, the test file that was already there, so
  the rule changed nothing for the file with 5 of the 12 later commits. To force more than a skip,
  the guard would have to be new, or fail on some mutation of the file.
- **Red grouping didn't happen.** Both runs still wrote 8 separate `env: uharfbuzz` lines (10 red
  slots in all). The agent's pytest command had no `-rf`, so maybe no `FAILED x - message` lines
  were printed to group on. Not checked yet.

Spend for the arm: untangles $2.31, probes $5.43.

## Next

A gain from untangle can't be measured on this repo with these probes. Five arms, including the one
that restructured a probe's area, sit inside the noise of an untouched probe (D3). The options:

1. Probes whose report doesn't point at the file: a UI-only symptom, or a feature that cuts across
   modules. That is the case where structure decides how much an agent searches.
2. A second repo, with more later commits landing in code the untangle can move.
3. Fix the two 1.41.0 findings above whatever the eval shows: a skip guard must be new or mutation-checked, and
   reds must group without `-rf`.
