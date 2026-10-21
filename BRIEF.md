# Automatic verification progression

User request: develop the automatic progression design discussed in this chat.

## Decisions
- Add an opt-in `verify.py advance` entry point around the existing feature state machine.
- Mechanically execute check runs and safe baseline freezing; return structured tasks for requirements, proof design, repairs, and independent judgment.
- Preserve strict proof gates, existing commands, state storage and leases. Never execute the human-readable NEXT string.
- Bound automatic actions, reject stale plans, respect foreign leases, stop when no progress is possible, and report each executed action.
- Default assumption: checks in the project's VERIFY.md are authorized commands, as with `run`; they can have their own side effects. Advance itself edits no product, checks, or recipe.

## Acceptance
CLI integration checks cover progression to strict green with real rejection evidence, decision/blocked stops, no repeated execution on unchanged inputs, budget and input validation, stale plans, and foreign claims.
