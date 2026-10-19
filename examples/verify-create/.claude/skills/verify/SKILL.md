---
name: verify
description: >-
  Launch, drive and prove the notes service (HTTP API on 127.0.0.1:8765) the way a client does,
  with evidence. Use to verify a change here, check note create/reject behavior in the running
  service, or prove a task done. Verdicts come from VERIFY.md through verify-loop.
---

# Verify the notes service

Written for an agent reading it cold. Pass/fail is never decided here: each mapped feature has a
check in [VERIFY.md](../../../VERIFY.md) with a literal `fail-signal:` and a `fail-proof:`, and
verify-loop's `verify.py` runs it. This file says how to reach and watch the real service.

Surface: one HTTP JSON API (`app.py`, stdlib). No UI, no CLI, no auth. Commands run from the
project root (the folder holding `app.py`).

## Launch

```bash
python .claude/skills/verify/scripts/notesctl.py seed      # fresh .verify-data/ with "Grocery list"
python app.py --port 8765 --data .verify-data & echo $! > .verify-pid
python .claude/skills/verify/scripts/notesctl.py ready     # repeat until exit 0
```

Ready means `GET /health` answers `ok` and the seeded store is readable. VERIFY.md `## Run` holds
the same setup/start/ready/doctor, so `verify.py run` launches, checks and tears down by itself.
Isolation: one instance per port and data dir. Another port needs `--port N --data DIR` on both
`app.py` and every `notesctl.py` call; never drive an instance you did not start.

## Doctor

`python .claude/skills/verify/scripts/notesctl.py doctor` — read-only. It compares the instance's
`/health` build digest with `app.py` on disk (uncommitted edits included) and its data file with
`.verify-data/notes.json`, printing `DOCTOR MISMATCH <field>: expected …, observed …`. A healthy
old process after an edit fails here: relaunch. Run it first and after any surprising result.

## Drive

Harness: plain HTTP through `notesctl.py` (urllib; curl works the same). Routes: `POST /notes`
`{"title","body"}`, `GET /notes`, `GET /health`. One file per feature in
[features/](features/README.md):

```bash
python .claude/skills/verify/scripts/notesctl.py drive create-note
python .claude/skills/verify/scripts/notesctl.py drive reject-empty
```

## Evidence

Each drive records the request, status, response, `GET /notes` and the store before and after in
`.verify-evidence/<feature>/run.json` (git-ignored), and prints the path. The store read is the
side effect check: a 201 alone is not proof. No mocks: the real server and file store are used.
Output tails and rejection receipts also stay in `.verify-state.json`.

## Cleanup

```bash
kill "$(cat .verify-pid)" && rm -f .verify-pid && rm -rf .verify-data
ls .verify-evidence/*/run.json   # the proof must still be here
```

Kill only the PID you started; never by process name. `verify.py run` stops its own instance.

## Helpers

`scripts/notesctl.py` (executable) — `seed`, `ready`, `doctor`, `drive create-note|reject-empty`;
options `--port 8765 --data .verify-data --evidence .verify-evidence`. Its docstring lists them.

## Verdict

`<verify-loop>` is the installed verify-loop skill's directory. Every caller gets its answer:

1. Prove a feature can fail: in a scratch copy, put the product in its `fail-proof:` state and run
   `python <verify-loop>/scripts/verify.py run .` until its `fail-signal:` shows; restore.
2. Freeze: `verify.py baseline .`. A check that seems wrong is a finding for a person, not an edit.
3. Done: `verify.py run . --strict`, then `verify.py report .` (or `status --json`). Return that
   output unchanged: verdict, `VERIFY:` line, observed rejection, passes and gaps.

Never weaken a journey or expectation to make it pass. If verify-loop is absent, run the checks
directly before and after, keep both outputs, and report the verdict as `unverified`.
