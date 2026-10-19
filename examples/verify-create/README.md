# Create mode example

A tiny stdlib notes service (`app.py`, spec in `SPEC.md`) with a project verify skill made by
create mode: `.claude/skills/verify/` (SKILL.md, `features/`, `scripts/notesctl.py`) wired to
`VERIFY.md`. To reproduce from the plugin repo root:

```bash
V=plugin/skills/verify-loop/scripts/verify.py
python $V skill-check examples/verify-create         # shape: ok
python $V run examples/verify-create                 # launches on :8765, doctors, drives, stops
```

How it was made and proved: write VERIFY.md sections, run `scaffold-skill`, fill in every
`TODO(verify-create)` from the repo, follow the skill by hand (launch, doctor, drive
`create-note`, clean up, and check that `.verify-evidence/create-note/run.json` still exists),
edit `app.py` without committing it and see the doctor reject the old process, put each feature
in its `fail-proof:` state and see its `fail-signal:` from `verify.py run`, restore, then run
`baseline`, `run --strict` and `report`. The resulting state is local and git-ignored, so a fresh
checkout starts at `unverified` until you repeat those steps.
