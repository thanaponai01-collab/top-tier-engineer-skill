I added `fixture/CLAUDE.md`, which Claude Code loads automatically at the start of every session in this repo. It lists each command, what it does, and whether it writes to `notes.json`. It also covers the risks, how to test without touching the real notes, and how the code is laid out.

Everything in it comes from reading the source and running the commands. I only ran the read-only commands (`--help`, `list`, `search`, `sync`) on your real notes. I tested `export` on a throwaway copy, and your notes weren't changed.

What I found:
- **`export notes.json` deletes all your notes.** The export command empties the output file first and reads the notes second. If the output file is `notes.json` itself, it ends up empty and the command crashes. I confirmed this on the copy.
- **`sync` doesn't work.** It shows up in `--help`, but nothing is connected to it in `notes.py`, so it crashes with a `TypeError`.
- **Other risks:**
  - `purge --yes` deletes everything with no undo.
  - Saving isn't atomic, so if a write is interrupted it can corrupt `notes.json`.
  - If `notes.json` is missing or empty, every command crashes.
- **`search` doesn't look at tags.** It only matches text in titles and bodies.

I didn't fix any of these bugs; the file only documents them. The `export` and `sync` fixes are small if you want them.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: agent guide

Read this before you run anything here. `notes.json` holds the owner's **real notes**, and several
commands write to it directly. There is no backup, no undo, and no git history.

Entry point: `python notes.py <command> ...` (stdlib only, no install step). Last checked with Python 3.13.

## Commands

| Command | What it does | Touches `notes.json`? |
|---|---|---|
| `list [--tag T]` | Prints `#id title  [tags]`. `--tag` takes one tag and matches it exactly. | read |
| `search QUERY` | Case-insensitive substring match on **title and body only** (not tags). Prints `#id title`. | read |
| `add TITLE BODY [--tag T]...` | Appends a note with id = max id + 1. Repeat `--tag` to add more tags. | **writes** |
| `export PATH` | Writes every note to PATH as JSON. Overwrites PATH without asking. | read (see hazard below) |
| `purge --yes` | Deletes ALL notes. Without `--yes` it prints "refusing" and exits 1. | **writes (destroys)** |
| `sync` | Shows up in `--help` but **isn't implemented**. It crashes with `TypeError: 'NoneType' object is not callable` because it has no entry in `HANDLERS` in `notes.py`. | no |

`list`, `search`, `--help` and `sync` are safe to run on the real data.

## Hazards (verified)

- **`export notes.json` wipes the store.** `commands/export.py` opens PATH for writing, which truncates
  it, and only then reads the store. When PATH is the store, the result is an empty `notes.json` and a
  `JSONDecodeError`. Never export to `notes.json`.
- `purge --yes` cannot be undone.
- Writes are not atomic (`store.py` dumps straight into the file), so an interrupted write can corrupt the store.
- A missing or empty `notes.json` makes every command crash.

## Testing changes safely

Never exercise write commands against the real store. `store.PATH` is resolved next to `store.py`, so
work on a copy:

```sh
T=$(mktemp -d) && cp -r notes.py store.py commands notes.json "$T"/ && cd "$T"
python notes.py add "t" "b" --tag x   # only touches the copy
```

## Layout

- `notes.py` holds the argparse definitions and the `HANDLERS` dict that maps each command name to `run(store, args)`.
  To add a command, add a subparser **and** a `HANDLERS` entry. Leaving out the entry is how `sync` broke.
- `store.py` has `Store.all()` and `Store.save(notes)`, which read and write `notes.json` next to the file.
- `commands/*.py` has one module per command. `list` lives in `listing.py`.
- Each note looks like `{"id": int, "title": str, "body": str, "tags": [str]}`.
