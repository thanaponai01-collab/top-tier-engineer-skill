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

## Next

1. Run two fresh untangle 1.41.0 trees (Opus, about $3), add them with `SP_ARMS`, and run the six
   probes on both (about $6). This is the first arm that should change the files the probes hit.
2. If 1.41.0 also ties, a gain from untangle is unmeasurable on this repo with these probes. The next
   lever is probes whose report does *not* point at the file (a symptom seen from the UI only), or a
   second repo.
