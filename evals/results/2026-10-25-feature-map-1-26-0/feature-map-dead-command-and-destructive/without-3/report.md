I added `fixture/AGENTS.md`, which documents what the CLI can do. I also added `fixture/CLAUDE.md`, a one-line file (`@AGENTS.md`) that makes Claude Code load those notes automatically at the start of each session.

**What the file covers:**
- **Every command:** its arguments, what it prints, and which files it writes. I ran each one to check. I tested `add`, `purge` and `export` on a throwaway copy of the folder, so your real `notes.json` wasn't changed.
- **A data-safety warning at the top:** the CLI always writes to the `notes.json` next to `store.py`, no matter which folder you run it from, and there's no option to point it at a different file. Any test of `add` or `purge` would hit your real notes, so the file includes a one-line recipe for testing on a temporary copy instead.
- **Code layout:** the note format, and how to add a new command (write a handler in `commands/`, then add it to `HANDLERS` in `notes.py`).
- **Known issues:**
  - **`sync` is broken:** it shows up in `--help`, but there's no code behind it, so it crashes with `TypeError: 'NoneType' object is not callable`.
  - **Search ignores tags:** `search` only looks at titles and note text.
  - **`export` overwrites silently:** it replaces an existing file without asking.
  - **Missing `notes.json` crashes everything:** every command fails if the file is missing or invalid.
  - **Saves can corrupt the file:** a crash while saving can leave `notes.json` damaged.

I didn't fix any of these bugs because you asked for documentation only. If you'd like, I can fix `sync` next: either remove the command or make it print "not implemented".

<!-- file written by the agent: fixture/AGENTS.md -->
# Agent notes: `notes` CLI

Verified by running every command (2026-10-25). Update this file if you change the CLI.

## ⚠️ Data safety first
`notes.json` holds the owner's **real notes**. `store.PATH` is fixed to the `notes.json`
next to `store.py`, whatever the cwd, and **there is no flag or env var to point it somewhere else**.
So `add` and `purge --yes` always write to the real file. To try a command that writes,
copy the repo to a temp dir and run it there:

```sh
T=$(mktemp -d); cp -r . "$T"; cd "$T"; python notes.py add t b   # safe
```

Read-only commands (`list`, `search`, `--help`) are safe to run here.

## Layout
- `notes.py`: argparse setup plus a `HANDLERS` dict that maps each subcommand to `commands/<mod>.run(store, args)`
- `store.py`: `Store.all()` / `Store.save(notes)`, which read and rewrite the whole JSON list
- `commands/`: one module per command (`list` is in `listing.py`)
- Note schema: `{"id": int, "title": str, "body": str, "tags": [str]}`
- Pure stdlib, no dependencies, no tests, no git.

## Commands (`python notes.py <cmd>`)
| Command | Effect | Writes? |
|---|---|---|
| `add TITLE BODY [--tag T]...` | Appends a note with id = max+1 and prints `added #N`. `--tag` can repeat. | notes.json |
| `list [--tag T]` | Prints `#id title  [tags]`, filtered by one exact tag | no |
| `search QUERY` | Case-insensitive substring match on title and body (**not tags**). Prints `#id title`. | no |
| `export PATH` | Dumps all notes as JSON to PATH and **overwrites it without asking** | PATH |
| `purge --yes` | Deletes ALL notes and appends a line to `purge.log` next to notes.json. Without `--yes` it prints "refusing without --yes" and exits 1. | notes.json, purge.log |
| `sync` | **Broken.** It's in the parser but has no entry in `HANDLERS`, so it crashes with `TypeError: 'NoneType' object is not callable`. There is no cloud code anywhere. | no |

## Known gaps
- If `notes.json` is missing or invalid JSON, every command crashes. Nothing creates the file.
- There is no edit/delete for a single note, only `purge` for everything.
- Saves are not atomic: `save` opens the file with `"w"` and dumps into it, so a crash mid-write can corrupt the notes.
- Back up `notes.json` before any change to `store.py` or `purge`.


<!-- file written by the agent: fixture/CLAUDE.md -->
@AGENTS.md
