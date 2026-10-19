# Create note

A client posts a titled note and gets it back with an id; the note is stored and every later
listing includes it.

verify-section: Create note

## Sub-features

- `create-save` POST with a title returns 201 and the note.
- `create-list` `GET /notes` lists the new note.
- `create-store` the note is in `.verify-data/notes.json`.

## How to get to it (user POV)

- `POST /notes` with JSON `{"title": "...", "body": "..."}`. This is the only entry point.

## Driving it with notesctl (HTTP)

Preconditions:

- Doctor ok; no note titled `Release checklist`.

- **Create.** `python .claude/skills/verify/scripts/notesctl.py drive create-note` posts
  `Release checklist` / `Tag and publish`. Status 201 and the note with an id.
- **Read back.** The same run lists `GET /notes` and reads the store: both contain it.
- **Proof.** `.verify-evidence/create-note/run.json` holds status, response, listing and the
  store before and after.

## Gotchas

- Titles are trimmed on save; assert the stored title, not the posted one.
- A second run without reseeding adds a duplicate; the check still passes, the ids differ.
