# Verification preparation and validation

Load for new/stale check definitions or evidence. Reuse current receipts when their declared inputs
and requirements are unchanged; do not rerun checks once per document or checkpoint. Snapshot
hashes aid discovery but never replace the verifier's baseline/evidence validity checks.

Resolve verify-loop from the installed plugin/skill location; do not assume its scripts live in
the target repo. Read its SKILL.md, VERIFY_FORMAT.md and relevant challenge reference and run the
bundled helper's --help. Those files own the exact format and mutation schema. Optional init is a
draft generator; finish the selected recipe instead of announcing readiness with TODOs. Trace
unsupported stacks by hand; zero discovered entries does not mean zero features.

## Validate selected behavior

Run the behavioral check on the unchanged product. Complete verify-loop's actual rejection proof,
baseline, run --strict and current status with this project as the repo argument. Prefer challenge
for a controlled product mistake in scratch copies, leaving source behavior unchanged. Declare
all tests, fixtures, imported check helpers and expectation files before collecting proof. Every
feature claimed verified needs its own rejection evidence; one caught mutation does not certify the others.

Repair empty/disconnected checks only when their intended requirement is established, disclose
check edits, and regenerate proof. A discovered product defect blocks readiness unless the user
also requested its repair. Preserve unrelated failures and unmapped tests; never delete or weaken
checks to obtain green. Retain outputs and state rather than writing prose-only proof.

If verify-loop is unavailable, prepare a useful draft and execute existing checks directly.
Report draft / verifier unavailable, not strict verified readiness. Explain which installed skill
or reviewed runner is needed; do not silently fetch a moving runner.

Repeat discovery after validation: re-read the instructions, manifests, selected entry point and
recipe; compare setup-file hashes from the first completed pass. Re-running checks alone is not
the second setup pass. An unchanged setup leaves completed files unchanged; reuse
only current evidence. Changed inputs require updating affected recipes and regenerating stale
proof. Compare original/final files, confirm source behavior remains unchanged, and disclose edits.
