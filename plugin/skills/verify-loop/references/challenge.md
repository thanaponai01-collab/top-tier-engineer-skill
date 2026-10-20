# Challenge the check

Use when asked to challenge verification, or when a green check may not observe the product.
Choose one plausible mistake that violates the claim: flip a sign, move a boundary, remove
an authorization guard or return a wrong value. Use the spec to say why it is wrong.
Do not generate a broad mutation campaign for proof; use the auto survey below only when asked
how strong a check is (a mutation score) or to hunt for weak spots.

Read VERIFY.md and choose an exact feature name. Declare a literal `fail-signal:` that names
the intended behavioral rejection. For reusable strict verification, also record `fail-proof:`
describing the mutation. Select product code outside the frozen tests and oracles.

Write a small JSON mutation file in the project, for example:

```json
{
  "file": "refund.py",
  "before": "credit + amount",
  "after": "credit - amount",
  "claim": "A refund increases available credit by the refund amount."
}
```

Run the bundled helper; it does the mutation in fresh scratch copies:

```bash
python <skill-base>/scripts/verify.py challenge . --feature Refunds --mutation mutation.json
```

The original recipe must pass first. Both copies execute the full recipe, including setup,
launch, doctor and cleanup. The target feature decides the mutation verdict:

| Verdict | Exit | Meaning |
|---|---|---|
| caught | 0 | A behavioral check rejects the mutation with its declared signal |
| survived | 1 | The target feature's checks still pass on the wrong implementation |
| inconclusive / invalid | 2 | Original is red, mutation is ambiguous, harness failed, signal did not match or checks changed |

A surviving mutation is a coverage finding. When asked only to diagnose, report it without
editing. When implementing verified behavior, repair the check before its baseline, then
challenge it again. Never change the expected outcome to fit the implementation.

Evidence is stored under `challenge` in .verify-state.json: claim, exact mutation, original
tree fingerprint, check signature, commands, exit codes and bounded output for both runs.
With `require: challenge` in VERIFY.md, strict stays red (`UNCHALLENGED`) until one
challenge is caught for the current checks. Caught evidence can satisfy strict rejection proof for unchanged checks; still run `baseline`,
`run --strict` and `status` before claiming completion. Challenge alone does not mark the regular
verification state green. Evidence becomes historical when files or check definitions change.
Caught checks also retain individual receipts under `failures`, including their mutation and
source fingerprint. Challenging another feature preserves these receipts; changing the frozen
check signature invalidates them. The `challenge` object holds the latest full experiment.

Scratch copies preserve uncommitted files and reject symlinks and directory junctions. Checks
must use local copies of code and fixtures; live checks need a scratch-local Run start recipe.
The runner rejects evidence if a trial overwrites its product mutation or changes frozen checks.
Copies provide filesystem separation, not an OS sandbox: absolute paths, external services,
ports and credentials still need project-specific isolation. Use trusted recipes and redact
sensitive output. One caught mutation proves detection of that mistake, not complete coverage.

## Auto survey (mutation score)

```bash
python <skill-base>/scripts/verify.py challenge . --feature Grade --auto app.py [--max 20] [--jobs N] [--json]
```

Generates standard syntax-validated mutations for one product file (flip `==`/`!=`, move a `<`/`>=`
boundary, swap `and`/`or`, flip booleans, swap `+`/`-`, swap `*`/`/`, invert `is`/`is not`, mutate
`return` to `return None`, off-by-one integers, drop `not`). Two operators that produce the same line
count once, and a Python mutant whose syntax tree equals the original is dropped.

The tree is copied once per lane. The feature's checks must pass there unmutated, then each mutant is
written in, judged against **that feature's checks only**, and reverted. A lane whose checks leave
other files changed is recopied before the next mutant. `--jobs N` runs N lanes in parallel: worth it
when checks are slow, not when copying the tree dominates. A `## Run` recipe forces one lane, since
one app holds one port.

Each survivor's line then gets a probe: an abort inserted before it. If every check still passes, no
check reaches that line and its mutants are reported `UNCOVERED`, not `SURVIVED`: the gap is a missing
check, not a weak one. Lines where a probe cannot be inserted safely stay `SURVIVED`. The score is
`caught / (caught + survived + uncovered)`. Exit 0 all caught, 1 any survived or uncovered, 2 nothing
decided.

Generated mutations come from the code, not the spec, so the survey **never records fail-proof
receipts or touches .verify-state.json**. A survivor is a lead: judge it as a real gap (write a
spec-backed check, then prove it with a normal `--mutation` challenge) or an equivalent mutation
that changes no observable behavior. A high score on one file is not coverage of the feature.

### Only what changed: --diff

```bash
python <skill-base>/scripts/verify.py challenge . --feature Grade --auto app.py --diff [REF]
python <skill-base>/scripts/verify.py challenge . --feature Grade --auto --diff [REF]
```

`--diff` (default `HEAD`) mutates only lines added or changed since REF, uncommitted edits
included; an untracked file counts as all new. With no FILE it surveys every changed product file in
Python, JS/TS, Go or Rust, and skips tests, oracles, the recipe and other files. Use it to ask
"would the checks catch a mistake in *my change*?" in seconds rather than surveying whole files.
Same lanes, verdicts, probe and exit codes as a whole-file survey; `--max` caps the total, and
JSON adds `diff`, `files` and a `file` per result. A change that touches no mutable line (comments,
strings, deletions only) exits 2: there is nothing to score.

## Machine-readable reports

`verify.py status --json` prints the same verdict and exit code as `status`, plus `failing`
checks, `receipts`, `strict`, `rounds` and the last `challenge` verdict, for callers that gate on it.
`verify.py run --json` outputs the full structured verification report, including feature summaries and check exit codes.
