# Sonnet replay probes for untangle

Question: does an untangled tree make a weaker agent's **next real change** cheaper and safer?
The Opus probes in `../2026-11-07-untangle-compare/` could not tell (orig 5/6, every arm ~10-11/12),
because Opus finds the fix on any tree. This eval keeps the same trees and swaps in a Sonnet probe
agent plus effort and damage scores.

## Probes

All are real Transcriber_v2 commits after the cutoff `b3922e1`, chosen because their code diff applies
at the cutoff and they ship tests. `python harness/sp.py check` proves each one: hidden tests red on
the cutoff tree, green with the real fix applied (6/6 VALID, 2026-11-07).

| id | commit | kind | area |
|---|---|---|---|
| D1 | 21dbb5a | fix | nativeCut.js read-back retry |
| D3 | f333ad4 | fix | sync_plan.py coarse pieces |
| D4 | a8d613c | fix | cues/split.py empty pair (prompt reworded: it now names the engine file the traceback names; the old wording sent Sonnet into the faster-whisper library) |
| P5 | a9f1d89 | fix | faster_whisper.py floored seek |
| P6 | 09c52a6 | fix | nativeCut.js razor filler between frames |
| P7 | 60e1b66 | feature | nativeSync.js sync the original of a _Synced copy |

Left out: b386552 and 00a809e (build on 09c52a6, don't apply at the cutoff), b6f41d0 and 39bdee0 (no test).

## Scores per run

- `ok`: only the commit's own new or changed tests, selected by name, pass (later test files also
  hold tests for earlier fixes the tree never got).
- `damage`: tests green on the arm's tree before the probe and red after (full pytest + node suites).
- effort: true cost (last cumulative `total_cost_usd`), tokens, tool calls, distinct files read,
  calls before first touching the real fix file.
- `stray`: non-test files changed that the real fix didn't touch (reported only; a fix elsewhere can
  be valid).

## Arms

Existing committed trees from the compare run: `orig`, plain Opus `U1 U2`, ours (1.38.0 draft)
`O1 O2`, caldoai `C1 C2`. A 1.41.0 arm needs fresh untangle runs; add its trees with
`SP_ARMS="N1=<repo>;N2=<repo>"`.

## Run

```
python harness/sp.py batch orig,U1,U2,O1,O2,C1,C2 D1,D3,D4,P5,P6,P7 2
python harness/sp.py table
```

Runs and trees live in the session scratchpad (`SP_WORK`); `data/probes.json` gets the rows.
Smoke: `orig-D4-1` ok, $0.25, 18 calls, 9 files read, fix file at call 11, no damage.
