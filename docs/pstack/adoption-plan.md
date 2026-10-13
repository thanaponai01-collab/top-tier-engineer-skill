# PStack adoption plan

Status owner: [handoff](../../work/pstack-handoff.md). Evidence: [validation](validation.md).
P01 was authorized by the user's `/drive implement the p01` request; its bounded results are
in [evidence](../../work/p01/evidence.md). P05 implementation and bounded trial evidence are in
[the P05 record](../../work/p05/evidence.md); adoption status remains handoff-owned. Other slices
retain their status in the handoff.

## P01 Establish trustworthy behavioral evidence

Inspect evals/agent.py, evals/run.py, transcript parsing and graders. Verify isolation and reconcile
direct SKILL.md reads with Skill-tool calls. Use the existing harness. Acceptance: the pilot records
the staged skill actually read, distinguishes parser misses from absent reads, independently checks
the result, and separates loading, procedure and outcome. Repeat before claiming reliability or savings.
Start with one fresh-reader/recovery case rather than rerunning every historical case.

## P02 Exercise the existing application recipe

Placement: verify-loop's project-recipe reference and existing eval fixtures/helpers. Start with one
surface, then browser UI, API service and short-lived CLI as separate trials. Exercise isolated launch,
usable readiness, owned expected build, public entry path, observable effect, rejection/pass and cleanup.
Acceptance: detect an old server on the expected port; preserve readable evidence after teardown;
leave no owned residue; never terminate unrelated instances. Reopen/query persisted writes through
a second path. Distinguish missing prerequisites, harness failure and product failure. One surface
does not establish support for others; a generated driver stays draft until exercised meaningfully.

## P03 Enforce one repeated mistake

Placement: the helper/module owning the invariant, plus its regression and behavioral case. Select
a mistake class with two actual occurrences. Prefer removing the invalid path/duplicate owner, then
types where applicable, actionable lint/runtime enforcement, then tests. Keep rules for judgment.
Acceptance: unchanged enforcement rejects the old mistake and accepts the valid result, explains
the correction and does not silently allow exceptions. Reuse local/CI commands. Avoid a whole-repo
refactor or generic rule engine. A new instruction alone does not complete this slice.

## P04 Strengthen benchmark validity

Placement: a short perf-optimize reference used when measurements guide decisions. Record workload,
useful work count, errors, output correctness, fair configurations and limiter. Alternate comparable
runs, report variation, and measure the user journey alongside micro results. Profile separately.
Acceptance: reject a fast no-op/error-heavy result and unfair debug-versus-release comparison;
report noise as inconclusive. Bound effort; do not impose an arbitrary minimum iteration count.

## P05 Offer independent design candidates

Placement: arch-design's existing flow/reference. Trigger for uncertain ownership, concurrency,
costly public/stored contracts or consequential competing shapes. Define criteria first, isolate
structurally distinct sketches, include the simplest viable option and verify any synthesis.
Acceptance: a consequential fixture exposes alternatives and explains the selected tradeoff; a
routine fixture avoids extra ceremony. Bound seats/time/cost. Unsupported hosts disclose fallback
and never claim model diversity they did not use. Direct settled small changes remain supported.

## P06 Test decisive safety assumptions

Placement: scrutinize and existing verification handoffs. Identify the one or two assumptions
making a change safe. Follow relevant formats, schemas, lifecycle ordering, pinned libraries and
flags beyond direct callers. Acceptance: an unchanged consumer/boundary fixture exposes a real
regression; a small probe rejects bad behavior and confirms safe behavior. Source reading is traced,
not proven. State unknowns rather than inventing a comprehensive impact map.

## P07 Validate actual running artifact identity

Placement: existing VERIFY.md Run/Doctor and verifier evidence. Record material build/source/dirty
identity, flags, roles and mocked boundaries. Inspect existing fields first. Acceptance: relevant
build/configuration changes invalidate or limit old proof; a healthy old process is rejected.
HEAD alone must not identify an uncommitted build. Reuse receipts; add only demonstrated missing data.

## P08 Clarify standalone use and composition

Inventory installed-skill handoffs and missing-skill fallbacks before editing promises. Keep generated
skill lists canonical. Acceptance: standalone/composed behavior is accurately described; a missing
dependency follows a stated fallback or explicit limit; direct small tasks remain supported.
Keep explanations at existing authoritative homes, without duplicating another skill inventory.

## Order and scope

P01 comes first. Design P02/P07 fixtures together to avoid repeated startup/proof work. P03/P04
follow once reporting is trustworthy; P05/P06 need independent discrimination cases. Shared edits
have one writer. Before skill changes, write a case, retain baseline and replay after. Consult
current context and diffs; do not overwrite unrelated work or replace an active RUN.json.
Version bumps, releases, installed-plugin updates, tracker filing and P09 are outside this
document-authoring task. Later adoption follows repository checks and the user's actual scope.
