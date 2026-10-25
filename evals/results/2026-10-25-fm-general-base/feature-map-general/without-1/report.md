I read every source file and ran the risky paths against a temporary copy of `pantry.json` (via `PANTRY_DB`). Its checksum was the same before and after, so your real pantry is unchanged. The repo's `AGENTS.md` matches the code. Run everything from `fixture/`.

**1. Marking one unit as used (web).** Each row has a **"Use 1"** button (`data-testid="use-btn"`, with `data-id` set to the item id). Clicking it sends `POST /api/items/<id>/use` with the JSON body `{"n": 1}` (`web/static/app.js:23`). The server replies 200 with the updated item, or 400 `{error}` if the id is unknown or there isn't enough stock. The "+1" button next to it sends the same request to `/restock`.

**2. Shopping list from the command line.** Run `python pantry.py shop`. An item goes on the list when its `qty` is less than its `min`, and the amount to buy is `min − qty` (`store.py:57`). On your data it currently prints `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. Olive oil (1 of min 1) isn't on it because the check is strictly "less than". The same list is at `GET /api/shopping-list` and behind the page's **"Shopping list"** link.

**3. Keyboard shortcuts.** There are two (`app.js:47-55`):
- `/` focuses the search box. Typing there filters the list as you type.
- `Ctrl+Enter` submits the add-item form.

**4. Moving the pantry with export and import: no.** `python pantry.py export out.csv` works, but `python pantry.py import out.csv` crashes with `KeyError: 'quantity'`, which I reproduced. Export writes a `qty` column and import looks for `quantity` (`pantry.py:49`). Even with that fixed, import ignores the CSV ids and appends every row, so importing into a non-empty pantry creates duplicates. Neither command carries over the `used` log. For now, the way to move it is to copy `pantry.json` itself, or point `PANTRY_DB` at a copy.

**5. The "Usage stats" button: no.** It calls `GET /api/stats`, and `store.stats` crashes with `KeyError: 'qty'` (reproduced). It adds up `u["qty"]`, but usage log entries store `n` (`store.py:71`). Your pantry already has usage entries, so it always fails: the server drops the connection and nothing appears on the page.

**6. Adding an item by barcode: you can't.** `python pantry.py scan` doesn't exist and is rejected with `invalid choice: 'scan'`. The README is wrong. To add an item, use `python pantry.py add NAME QTY [--min N] [--unit U]`, the add form on the page, or `POST /api/items`.

**7. Debug view of the raw data: yes, but it's off by default.** `GET /debug/dump` returns the whole database as JSON, but only if the `PANTRY_DEBUG` environment variable was set when the server started. Otherwise it returns 404. Nothing on the page links to it. The server only listens on `127.0.0.1`, so only someone on the same machine can reach it. When it is on there's no login, so anyone local who knows the URL can see it.

**8. The function that changes the count when you press Use.** It's `store.use_item` (`store.py:36`). It checks there's enough stock, does `item["qty"] -= n`, adds `{id, n, at}` to the usage log and saves. The server calls it at `web/server.py:58`.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the whole database with `{"items": [], "used": []}`, so every item and the entire usage log are gone. There's no backup. It also appends `wiped` to a `wipe.log` file next to the database. Without `--yes` it refuses and exits with code 1.

Before you change anything, run `export PANTRY_DB=/path/to/copy.json` first. Every write command and the web server write to `pantry.json` by default. The 2 existing tests pass and use their own temporary file. Nothing tests stats, import/export, the CLI or the server.