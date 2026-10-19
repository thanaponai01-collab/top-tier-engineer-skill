# Notes service verification map

The maintained source for verifying what clients touch. Read this index before driving the
service, then use the matching feature file. Each file names its VERIFY.md section
(`verify-section:`), which holds the check, its literal `fail-signal:` and its `fail-proof:`.

## Baseline preconditions

- Launched per ../SKILL.md Launch on port 8765 with `.verify-data/`; `notesctl.py doctor` ok.
- Seed: one note, `Grocery list`. No note titled `Release checklist`.
- Never drive an instance this run did not start.

## Driving conventions

- Start each recipe from the baseline state (re-run `seed` and relaunch between recipes by hand;
  `verify.py run` reseeds once per run). Use the routes, never the store file, as the action.
- Restore seeded data after a mutation. Do not remove proof artifacts during cleanup.

## Feature entry contract

H1 title, one paragraph of user-visible behavior, a `verify-section:` line, then exactly four H2s:
`Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`. A journey
the seed data cannot complete fails and says why in `Gotchas`; never weaken it to pass. A proof
through one entry point does not verify the others this map lists.

## Features

- [Create note](./create-note.md)
- [Reject empty note](./reject-empty-note.md)
