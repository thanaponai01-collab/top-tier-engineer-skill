# Verify-loop trust baseline

The predeclared bar is in `verify-trust.json`: at least five valid runs per case,
95% task success, and zero observed grader-trap failures, separately for development
and held-out cases. An errored, timed-out, or leaked run blocks the batch. Missing
cases and missing trap results cannot earn a pass. Run both with and without the
skill to assess whether the skill improves behavior.

These are finite-sample observations. Grader traps measure unsafe approval and
unnecessary rejection on selected cases; they are a proxy, not a production
false-green rate. Task failures can mean missed findings, unfinished fixes, or
missing evidence. Inspect transcripts and action checks before attributing causes.
The runner's unit tests establish mechanical behavior, not agent reliability.

## Recorded historical baseline

`results/verify-loop-rewrite/summary.json` contains eight development runs, one per
case, with the skill on claude-sonnet-5-5. Six passed: 75% task success. Four
guardrail observations had no grader-trap failures. Total recorded cost was
$1.6690472 and mean duration was 34.65 seconds. There are no held-out runs.

The bar is **not met**: repeats and held-out evidence are missing, and task success
is below 95%. This is an archived observation, not a fresh test of today's skill.
Do not pool later tuned batches into it to manufacture repeat coverage.

## Reproduce and extend

Summarize one existing batch (exit 1 means the bar was not met):

```bash
python evals/verify_trust.py evals/results/verify-loop-rewrite/summary.json
```

The retained `verify-trust-baseline.json` records this result with source and policy
SHA-256 hashes. Pass `--output <path>` to retain another scorecard.

Before a new run, freeze the skill revision, policy, grader, model, and runtime.
Record their revisions alongside the batch's metadata. First run the eight
development cases with `evals/run.py --cases <development names> --repeats 5
--arms with,without --dry-run`, then execute with an explicit per-run spend cap.
Use the normal meaning grader and action checks; phrase-only grades are diagnostic.
Evaluate `verify-loop-healthy-check` only after tuning ends. Combine development
and held-out summaries only from the same frozen campaign, preserving every run.
Mark a new held-out case as development after its results influence a change;
replace it with an unseen case for the next campaign.

Fresh behavioral runs need the Claude CLI and authenticated access. This workspace
session had no Claude CLI, so no new agent runs were executed. The healthy held-out
fixture and scorecard have local mechanical checks; their presence supplies no
behavioral success evidence.

Local validation: eight scorecard/fixture tests and 37 eval-harness tests passed.
The existing verify runner suite ran 64 tests with two Windows teardown errors:
temporary directories remained held by launched processes. Its full suite is not
claimed passing in this environment.

## Growth decisions

Turn escaped defects into outcome-graded cases that reject broken work and accept
correct work. Prioritize stale evidence, wrong target identity, setup failures
mistaken for behavioral rejection, adjacent callers, and healthy decoys.

Keep `verify-loop` responsible for check execution and retained evidence;
`correctness-gate` owns oracle quality and broader mutations. Existing specialists
supply performance, abuse, reachability, and release claims through the handoff.

Add `verify-audit` only after independent evaluations or escaped defects repeatedly
show a distinct need to audit already-issued verification claims. Its proposed
boundary is read-only assessment of oracle justification, product observation,
change coverage, and evidence identity. Green execution alone does not justify
creating it. No new companion skill is introduced by this baseline work.
