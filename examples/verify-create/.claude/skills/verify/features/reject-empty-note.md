# Reject empty note

A client that posts a blank title gets 400 and nothing is stored.

verify-section: Reject empty note

## Sub-features

- `reject-status` a blank or whitespace title returns 400 `title required`.
- `reject-store` the store is byte-for-byte unchanged.

## How to get to it (user POV)

- `POST /notes` with a missing, empty or whitespace-only `title`.

## Driving it with notesctl (HTTP)

Preconditions:

- Doctor ok.

- **Post blank.** `python .claude/skills/verify/scripts/notesctl.py drive reject-empty` posts
  `"   "`. Status 400.
- **Store unchanged.** The run compares the store before and after: equal.
- **Proof.** `.verify-evidence/reject-empty/run.json`.

## Gotchas

- Only the whitespace case is driven; a missing `title` key shares the guard but is not driven.
