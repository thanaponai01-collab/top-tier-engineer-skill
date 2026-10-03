# Run contract

Use `python <drive directory>/scripts/run.py --repo <project> <operation>`.
The helper runs replay-safe checks as argv arrays without a shell. It never deploys or rolls back.
Read and trust commands before running them: a command called a check can still mutate a system.

Write a contract JSON, then `init <contract.json>`. This freezes the contract and oracle file hashes
in RUN.json; keep the contract and checks out of implementation scope. It does not overwrite a run.
Only one writer may operate a run at a time. Store redacted check output; commands must never print
secrets. `python` in argv resolves to the interpreter running the helper.

```json
{
  "goal": "Export preserves cents through the real CLI",
  "target": "local",
  "max_attempts": 4,
  "timeout_seconds": 60,
  "max_seconds": 3600,
  "criteria": [{"statement": "CLI emits 42.35 for the acceptance fixture", "stage": "prove"}],
  "oracle_files": ["acceptance.py", "BRIEF.md"],
  "stages": [{"id": "prove", "skill": "correctness-gate",
              "command": ["python", "acceptance.py"],
              "inputs": ["src", "acceptance.py", "BRIEF.md"]}],
  "actions": []
}
```

Stages name the selected playbook steps, including evidence of diagnosis before a bug fix. Each
check must exit nonzero on a wrong result. `inputs` names files or directories whose changes would
invalidate that evidence; include source, configuration, lockfiles and the check itself. New and
deleted files in named directories count. Missing inputs fail. Git and Python test caches are
excluded. Keep generated output outside input directories. `oracle_files` includes every acceptance
check, its dependencies, fixtures and the spec; local hashes detect drift, not hostile rewriting.
Independent CI or held-out checks must live outside the implementation agent's write permissions.
Map every criterion to a stage; no uncovered requirement can be quietly dropped.

`next` shows the next step and unresolved actions. Load that skill, do its work, then `check <id>`.
Checks advance in order and reserve an attempt before running, so an interruption consumes budget.
`finish` requires every step to have passed and reruns all checks against the final state; budget
for this extra run. Red or timed-out checks, changed oracles, uncertain actions and stale inputs
cannot yield a successful `status`. Save decisions and artifact/commit IDs in the supporting build
or release notes and include those notes as inputs of the relevant check.

## External actions and recovery

For a staging or production target, the last stages must be `ship`, then `watch`. Their checks
observe the exact released artifact/version and real journey, then health over a specified window.
The release note must name thresholds, rollout limits, cost cap, rollback command and authorization.
The helper bounds check duration and attempts, not cloud spending; configure provider/host caps.
If a required environment or independent check is unavailable, stop blocked; do not substitute mocks
and claim production success.

Declare each external mutation in `actions`, for example:

```json
{"id": "deploy-canary", "stage": "ship", "environment": "production", "required": true,
 "authorization": "User authorized this artifact at 5% traffic, up to $10, and rollback to v12",
 "probe": ["python", "ops/probe_release.py", "--artifact", "v13", "--traffic", "5"]}
```

Authorization must come from the user, with exact action, environment and limits. An empty string
means parked. Declare rollback separately, at the stage where it can be needed, with its own probe.
Mark actions essential to success `required: true`; conditional rollback is not required. Completion
rejects a missing or absent required action, even if a weak observation check says green.
An upfront grant can cover deployment, bounded widening and rollback; ask only for a scope change.
Recorded authorization is not authenticated by this helper: enforce it with host permissions.

1. `begin <id>` durably records unknown *before* calling the external tool. It rejects unauthorized,
   out-of-order, unresolved or already applied actions. Use the action ID as the provider's idempotency
   key where supported; pin artifact and target in the mutation and its probe.
2. Perform the authorized action. A timeout does not tell you whether it happened.
3. `reconcile <id>` runs its read-only probe: exit **0** = desired action applied; **3** = definitely
   absent and safe to retry; any other exit or timeout = unknown, no retry. A remote request still
   pending is unknown, never absent. Probe credentials must have read-only scope where possible.
4. After a crash, read RUN.json and reconcile unknown actions first. If applied, continue without
   replaying the mutation. If absent, `begin` allows a bounded retry. If unknowable, stop blocked
   with the exact inspection needed. Never mark an action applied from a chat summary.

A successful rollback resolves the incident but does not meet a goal of deploying the new version:
record a failed run and preserved evidence. `stop blocked|failed --reason ... --next ...` records
an honest terminal result. `status` still exits nonzero. `resume` retains evidence and attempts and
does not reset budgets; revised criteria or exhausted budgets need an explicitly revised run.
If RUN.json is malformed, `stop` preserves its bytes in RUN.invalid.<hash>.json before recording
the handoff. It cannot resume until the damaged contract/journal is recovered and reviewed.

## Enforcement boundary

When enabled, the optional Claude Stop hook checks RUN.json even in a resumed session with no source edits. It blocks
active or invalid runs repeatedly; complete evidence or an explicit blocked/failed handoff permits
the session to end. Repositories without RUN.json keep the previous one-time VERIFY.md reminder.
Other hosts should run `status` in their completion/CI gate. Deleting or rewriting local files can
bypass local enforcement. This package provides a durable workflow and evidence gate; it does not
provide a background agent scheduler, independent grader, credential broker or production adapter.
Connect the actual host's execution, CI and deployment tools before promising autonomous production.
