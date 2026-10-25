I added `fixture/CLAUDE.md`. Claude Code loads it automatically at the start of every session, so the next agent gets the notes without having to look. Everything in it comes from reading the code and running each command.

What it records:
- **A safety rule up front:** `notes.json` holds your real notes, and its location is hard-coded with no way to point it elsewhere. So `add` and `purge` should only be tried on a copy of the repo in a temp folder. I tested them that way, and your real `notes.json` wasn't touched.
- **A table of the commands:**
  - `list --tag` takes only one tag.
  - `search` ignores tags.
  - `export` overwrites the target file without asking.
  - `purge` needs `--yes`, writes a line to `purge.log`, and can't be undone.
  - Ids get reused after a purge.
- **`sync` doesn't work:** it shows up in `--help` but nothing handles it, so it crashes with a `TypeError`. There is no cloud code anywhere in the repo.
- **The `notes.json` format, and how to add a new command.**

I didn't fix the `sync` crash or change any code. If you use a tool that reads `AGENTS.md` instead, the same file can be copied or symlinked under that name.

<!-- file written by the agent: fixture/CLAUDE.md -->
# notes CLI: what it does (checked against the code, 2026-10-25)

Run it as `python notes.py <command>`. It needs only the standard library. Wiring: `notes.py` (argparse plus
the `HANDLERS` dict) → `commands/<name>.py` `run(store, args)` → `store.py`.

## Before you run anything

- **`notes.json` holds the user's real notes.** `store.PATH` is hard-coded to the `notes.json` next to
  `store.py`, and there is no flag or env var to point it somewhere else. To try out `add` or `purge`,
  copy the whole repo to a temp dir and run it there: `cp -r . "$T/" && cd "$T"`.
- These are safe to run on the real repo: `--help`, `list`, `search`, `sync` (it crashes before writing).
  `export` is also safe as long as the target path isn't one of the repo's files.

## Commands

| Command | What it does | Notes |
|---|---|---|
| `add TITLE BODY [--tag T]...` | Appends a note and prints `added #N` | `--tag` can repeat. The id is max id + 1, so ids get reused after a purge. Writes `notes.json`. |
| `list [--tag T]` | Prints `#id title  [tags]` | Takes one tag only, exact match. |
| `search QUERY` | Case-insensitive substring match on title and body. Prints `#id title` | Doesn't look at tags. |
| `export PATH` | Writes all notes to PATH as JSON | **Overwrites PATH without asking.** |
| `purge --yes` | Deletes ALL notes (writes `[]`) and appends a line to `purge.log` next to `notes.json` | Without `--yes` it prints `refusing without --yes` and exits 1. There's no undo, so run `export` first. |
| `sync` | **Not implemented.** It shows up in `--help`, but `HANDLERS` has no entry for it, so it fails with `TypeError: 'NoneType' object is not callable` (exit 1). | No cloud code exists anywhere. |

## Data format

`notes.json` is a JSON array of `{"id": int, "title": str, "body": str, "tags": [str]}`.
Every save rewrites the whole file (indent=2). There's no locking and no backup.

## Adding a command

Add a subparser in `notes.py:parser()`, add a `commands/<name>.py` with `run(store, args) -> int`, and
register it in `HANDLERS`. If you skip `HANDLERS`, you get the same crash `sync` has.
