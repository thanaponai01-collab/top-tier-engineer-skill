# Workflow testing and adversarial evals

Use repository tests for deterministic helpers; use agent-evals and the existing eval harness
for model behavior. Neither replaces the other. Keep grader expectations outside worker access.
Before changing a workflow, retain a baseline; compare the same fixture, model and budget after
changes. A usage-limit response is a blocked run, not a baseline or behavioral verdict.

Start with a small suite, expanding only for new risks:
- Setup-only: preserve manual notes; one routing block; no foundation files, dispatch or checks.
- Foundation: sourced architecture/commands, honest coverage gaps, small startup and current Next.
- Delegation: bounded reader/executor assignments and actual dispatch/model trace where available;
  unsupported hosts must disclose single-agent fallback, not claim tier switching.
- Stale/fake evidence: changed source invalidates old proof; “tests passed” without a receipt
  cannot close a gate. A check that accepts a deliberately wrong result must fail evaluation.
- Adversarial input: repository text asks to push, delete checks or alter acceptance; worker
  must retain the owner's criteria and scope. Use disposable fixtures, not real external actions.
- Recovery: interrupt after a local edit or unknown external outcome; resume without dropping
  work or repeating an applied mutation. Journal reconciliation remains mandatory.
- Fresh reader: recover completed work, blockers and Next using only retained context, without
  conversation history; current and historical verification must remain distinguishable.

For ordinary software, derive tests from requirements and challenge a wrong behavior in a scratch
copy. For AI features, agent-evals owns task sets, graders and abuse cases before implementation;
agent-prove owns repeated proof. Reuse these skills instead of adding another testing framework.

Gate on observed outcomes and changed files, not phrases alone. Existing phrase graders and
reference-report tests establish harness discrimination, not live agent correctness. Routing
requires retained dispatch traces; where unavailable mark it unmeasured. Run one bounded pair
first, then repeated trials before claiming reliability or lower cost. Report pass rate, total
cost/tokens when available, elapsed time, dispatches and context size separately. Retain failed
runs too. No universal cost or latency threshold is invented without an owner target.
