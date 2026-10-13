# P06 evidence — decisive safety assumptions

Status: **bounded behavioral pass; procedure validation partial**. P06 adds a short decisive-assumption step to `scrutinize` and strengthens the existing unchanged-caller case to require the safety contract and a bad/safe boundary comparison.

## Retained checks

- `python -m unittest discover tests -p test_evals.py`: 44 passed.
- `python work/p06/probe/check.py`: the unsafe optional lookup is rejected by the unchanged `billing.price_for` boundary (`TypeError`); safe missing-user behavior returns `1000`.
- `python evals/run.py --cases scrutinize-unchanged-caller --repeats 1 --arms with --jobs 1 --budget-usd 2`: 1/1 passed, 3/3 findings, skill call observed, $0.23, 36 seconds. Artifacts: [run folder](../../evals/results/2026-10-13-1419/).
- The live report identifies the billing contract break and says the branch raises TypeError and main returns 1000. Its action log shows the real boundary command, the scratch worktree, and cleanup. It does not separately narrate running the safe-control command; the independent retained probe covers both sides. This remains one smoke trial, not a reliability claim.
- `python -m unittest discover tests`: 494 passed in 106.469 seconds.
- `python tools/catalog.py --check`: 36 skills, every copy current, listing 4993/5000 characters.

## Run record limitation

The repository-root `RUN.json` is the completed P05 run. `run.py init` refuses to replace it and the helper hard-codes that root filename. Per Drive instructions, it was preserved. P06 stage outputs and hashes are retained in `work/p06/RUN.json`, using the same contract/stage fields and commands with enforcement explicitly labeled manual. No production, release, or plugin installation action was taken.
