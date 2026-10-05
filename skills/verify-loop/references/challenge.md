# Challenge the check

Use when asked to challenge verification, or when a green check may not observe the product.
Choose one plausible mistake that violates the claim: flip a sign, move a boundary, remove
an authorization guard or return a wrong value. Use the spec to say why it is wrong.
Do not generate a broad mutation campaign.

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
Caught evidence can satisfy strict rejection proof for unchanged checks; still run `baseline`,
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
