# Instruments and the optional file

Use these only when the repo is too big to read whole, or the question is about history. On a repo
you can read, reading beats tooling.

- **Import graph** (Python): `python <latent-audit base>/scripts/graph-audit.py <src> --edges edges.json`,
  then `python <arch-design base>/scripts/dep-map.py edges.json`. Lists cycles (file:line), the
  most-imported modules and how unstable each is, pass-through modules, Protocol/ABC seams with
  their implementer counts, and modules that import network, database or process libraries.
  Leads, not verdicts. Not Python, or scripts missing: grep the imports of the modules in question.
- **Change history**: `python <arch-design base>/scripts/change-map.py <repo> --json > change.json`
  gives modules touched per commit, file pairs in different modules that keep changing together,
  and hotspots. `dep-map.py edges.json --cochange change.json` shows which coupled pairs have no
  import between them: a shared format nobody named. Exclude on-purpose pairs with `--exclude`.
- **Rehearsal**: walk a likely change through the code and count the modules you edit. More than
  two for one change means something is drawn in the wrong place.

## When the user wants a file

Write `docs/arch-design.md` with `key: value` bullets: header (`at:` short sha, `question:`,
`verdict:`), then one block per finding (`where:`, `cost:`, `evidence:`) and per move (`cost:`,
`pays:`, `files:`, `owner:`, `callers:`, `door:`, `proof:`, `effort:`, `after:`). Then run
`python <arch-design base>/scripts/arch-design.py check <file>`: it fails on a missing field, a
file or line not in the repo, an unconfirmed one-way door, and reports STALE if files changed after
`at:`. Fix what it says before handing the file over.
