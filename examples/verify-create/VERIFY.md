## Create note
- path: app.py
- run: `python .claude/skills/verify/scripts/notesctl.py drive create-note`
- oracle: SPEC.md
- fail-signal: expected stored note 'Release checklist'
- fail-proof: app.py answered 201 without writing notes.json; the drive read the store back and went red; restored

## Reject empty note
- path: app.py
- run: `python .claude/skills/verify/scripts/notesctl.py drive reject-empty`
- oracle: SPEC.md
- fail-signal: expected 400 and an unchanged store for an empty title
- fail-proof: app.py dropped the empty-title guard; the drive saw 201 and a new stored note; restored

## Run
- setup: `python .claude/skills/verify/scripts/notesctl.py seed`
- start: `python app.py --port 8765 --data .verify-data`
- ready: `python .claude/skills/verify/scripts/notesctl.py ready`
- doctor: `python .claude/skills/verify/scripts/notesctl.py doctor`

## Blind spots
- one process on one port; concurrent writers to notes.json are not exercised
- no auth: the service has none, so no role checks exist
