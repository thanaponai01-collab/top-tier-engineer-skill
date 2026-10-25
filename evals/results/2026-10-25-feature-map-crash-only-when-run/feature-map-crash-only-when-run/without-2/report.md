I added `fixture/AGENTS.md`, a reference page for the CLI. I also added `fixture/CLAUDE.md`, which is just `@AGENTS.md`, so Claude Code loads the same page automatically and other agents can read `AGENTS.md` directly.

**What it covers:**
- **Data safety:** `notes.json` holds your real notes. Every command uses that file no matter which directory you run from, because the path is fixed in `store.py`. It gives a copy-to-a-scratch-folder recipe for testing the commands that change notes (`add`, `tag`, `purge`), and a warning that `purge --yes` deletes everything with no backup.
- **Layout:** where each command's code lives, the shape of a note, and that there are no tests or dependencies.
- **Command table:** arguments, whether each command changes notes, exit codes, and edge cases. For example, `search` doesn't look at tags, `list --tag` needs an exact match, and `debug-dump` exists but doesn't appear in `--help`.

**Problem found:** `export` is broken. It crashes with `ValueError: ... 'tags'` whenever there are notes. It only knows about the `id`, `title` and `body` columns, so a note's tags make it fail, and the CSV it leaves behind has only the header row. I wrote this down in the notes but didn't fix it. The fix depends on whether you want tags in the spreadsheet (add a tags column) or not (skip them). Tell me which and I'll make the change.

I only ran commands that don't change notes. The one test export went to a temporary folder and I deleted it afterwards. `notes.json` still has its 3 notes.

<!-- file written by the agent: fixture/AGENTS.md -->
# Agent notes for `notes`

Read this first; it saves re-reading the code. Last verified 2026-10-25 against Python 3.13.

## ⚠️ Data safety
- `notes.json` holds the owner's **real notes**. Don't lose or overwrite them.
- Every command reads/writes `notes.json` **next to `store.py`** (path is hardcoded in `store.py`,
  not cwd-relative, and there is no flag or env var to change it).
- To try out commands that write (`add`, `tag`, `purge`), copy the repo to a scratch directory and
  run it there:
  `cp -r fixture "$TEMP/notes-scratch" && python "$TEMP/notes-scratch/notes.py" add t b`
- `purge --yes` wipes every note with no backup. Don't run it in the real repo.

## Layout
- `notes.py`: argparse setup plus the `HANDLERS` dict that maps each subcommand to `commands/<x>.run(store, args)`.
- `store.py`: `Store.all()`, `Store.save(notes)`, and `Store.next_id()` (max id + 1). Each save rewrites the whole JSON file.
- `commands/*.py`: one module per subcommand. `list` lives in `listing.py`, `debug-dump` in `debug.py`.
- Note shape: `{"id": int, "title": str, "body": str, "tags": [str]}`.
- No tests, no dependencies (stdlib only), no git history.

## Commands (`python notes.py <cmd>`)
| Command | Writes? | Behavior |
|---|---|---|
| `add TITLE BODY [--tag T]...` | yes | Appends a note and prints `added #N`. `--tag` can be repeated. |
| `list [--tag T]` | no | Prints `#id title  [tags]`. `--tag` filters on an exact tag match. |
| `search QUERY` | no | Case-insensitive substring match on title and body only (tags aren't searched). |
| `tag ID NAME` | yes | Adds a tag, skipping duplicates. Exits 1 with `no note #ID` if the id doesn't exist. |
| `export PATH` | no (writes PATH) | Writes a CSV for spreadsheets. **Currently broken, see below.** |
| `purge --yes` | yes | Deletes ALL notes. Without `--yes` it prints a refusal and exits 1. |
| `debug-dump` | no | Prints the raw JSON. It's hidden from `--help` because it has no help string. |

## Known issues
- **`export` crashes** with `ValueError: dict contains fields not in fieldnames: 'tags'` whenever
  a note exists. `commands/export.py` uses `COLUMNS = ["id", "title", "body"]` and `csv.DictWriter`
  defaults to `extrasaction="raise"`. The output file is left with only the header row.
  Not fixed yet. The fix is either to add `tags` (joined) to the columns or to pass `extrasaction="ignore"`.
  Ask the owner which one they want in the spreadsheet.


<!-- file written by the agent: fixture/CLAUDE.md -->
@AGENTS.md
