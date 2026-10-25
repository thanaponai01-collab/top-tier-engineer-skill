I mapped the `notes` CLI into `fixture/FEATURES.md`. Five of its six commands work. `sync` is listed in `--help` but crashes every time.

**What's in the map:** one section per command (add, list, search, export, purge, sync). Each one has:
- a one-line description of what it does;
- how to run it;
- the path through the code: `HANDLERS` in `notes.py`, then `commands/<x>.py`, then `Store.all`/`Store.save`, then `notes.json`;
- a status saying how it's known, plus a warning on the commands that change data.

Above the sections, a short note explains how the CLI is put together and warns that `notes.json` holds your real notes.

**Proof:**
- I ran all five working commands and the results are saved in `fixture/.features/`. `list --tag home` returned notes #1 and #3, `search dune` returned #3, and add, export and purge each printed their success message.
- add, export and purge ran in throwaway copies of the repo. `notes.json` has the same hash as before I started, so your notes weren't touched.
- The map checker now passes with no problems: `python .features/features.py check --strict --rerun` exits 0. It re-runs every saved command and flags anything that has moved or broken since. A copy of it lives in `.features/`, so it works without this skill installed.

**Bug — `sync` crashes:** `notes.py` registers the `sync` command but `HANDLERS` has no entry for it. Running it calls nothing and exits 1 with `TypeError: 'NoneType' object is not callable`, and there's no cloud code anywhere in the repo. The map marks it as broken, and the failed run is saved in `.features/sync.json`. I didn't change the code. To fix it, either implement sync or remove it from the parser. Then re-run `prove` and update its entry in the map.

I also added two lines to `README.md` pointing to `FEATURES.md` and the check command. There's no VERIFY.md, so the map has no links to one and I didn't create one. `fixture/` isn't a git repository, so nothing is committed. Commit `FEATURES.md` together with `.features/`.

<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the `notes` CLI can do and how each feature is reached. Run as `python notes.py <command>`
from this folder. Keep it true: `python .features/features.py check --strict --rerun` tests every
entry point against the code and re-runs every recorded proof (.features/<feature>.json).

How it works: `parser` in notes.py declares the subcommands, `main` looks the command up in
`HANDLERS` and calls `commands/<x>.py :: run(store, args)`. Every note lives in `notes.json`
(`Store.all` / `Store.save` in store.py). That file holds the owner's real notes, so run anything
that writes with `features.py prove --copy` or in a copy of the repo.

## Add
- what: Save a new note with a title, body and optional tags; prints its new id.
- cli: `add` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/add.py > `save` @ store.py > `PATH` @ store.py
- effect: appends `{id, title, body, tags}` to notes.json; id = highest id + 1. `--tag` repeats.
- status: proven: `add Test hello --tag x` in a copy printed `added #4`

## List
- what: Show every note (id, title, tags), or only the ones with a given tag.
- cli: `list` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/listing.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `list --tag home` printed #1 Groceries and #3 Books

## Search
- what: Find notes whose title or body contains a word (case-insensitive).
- cli: `search` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/search.py > `all` @ store.py > `PATH` @ store.py
- status: proven: `search dune` printed #3 Books

## Export
- what: Write all notes to a JSON file at a path you choose.
- cli: `export` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/export.py > `all` @ store.py > `PATH` @ store.py
- effect: creates/overwrites the given file (no confirmation).
- status: proven: `export out.json` in a copy printed `exported to out.json`

## Purge
- what: Delete every note; refuses (exit 1) unless given `--yes`.
- cli: `purge` @ notes.py
- trace: `HANDLERS` @ notes.py > `run` @ commands/purge.py > `save` @ store.py > `PATH` @ store.py
- effect: overwrites notes.json with `[]`. Destroys real notes: never run outside a copy.
- status: proven: `purge --yes` in a copy printed `all notes deleted`

## Sync
- what: Advertised in `--help` as "sync notes with the cloud"; does nothing, it crashes.
- cli: `sync` @ notes.py
- trace: `main` @ notes.py > `HANDLERS` @ notes.py
- status: traced: BROKEN. `parser` declares `sync` but `HANDLERS` has no entry, so `main` calls None and exits 1 with TypeError (failed receipt .features/sync.json). No cloud code exists in the repo.
