I read every source file and checked the claims in `FEATURES.md` against the code. I ran the read-only commands and the two suspected failures (import and stats) against a scratch copy using `PANTRY_DB`. `pantry.json` was only read, never written. I did not run the web server or click anything in a browser.

**1. Marking one unit as used (web).** Each row in the item table has a **"Use 1"** button (`data-testid="use-btn"`, `web/static/app.js:14`). Clicking it sends `POST /api/items/<id>/use` with body `{"n": 1}` (`app.js:23`). The server matches that path with `ITEM_ACTION` (`web/server.py:9`). It returns 200 with the updated item, or 400 if the item doesn't exist or there isn't enough left.

**2. Shopping list from the command line.** Run `python pantry.py shop`. With your current data it prints `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. An item goes on the list when its `qty` is below its `min`, and the amount to buy is `min - qty` (`store.py:57`). Nothing adds items to the list by hand. You change what's on it by using stock (`use`), restocking (`restock`), or setting `--min` when you add an item. On the page, the **"Shopping list"** link sends `GET /api/shopping-list`.

**3. Keyboard shortcuts** (`app.js:47-55`):
- `/` jumps to the search box (unless the box already has focus).
- `Ctrl+Enter` submits the Add form, which is the same as clicking **Add**.

There are no others.

**4. Moving the pantry with export then import: no.** `export` writes a `qty` column (`pantry.py:39`), but `import` reads `row["quantity"]` (`pantry.py:49`). Importing a file made by `export` fails with `KeyError: 'quantity'`. Even after that's fixed, it still wouldn't be a full move:
- Export writes only items, so the usage log (`used`) is lost.
- Import gives each item a new id with `add_item` instead of keeping its old id.

To move the pantry today, copy `pantry.json` to the other machine, or point `PANTRY_DB` at it there.

**5. "Usage stats" button: no, it's broken.** The button sends `GET /api/stats`. `store.stats` adds up `u["qty"]` (`store.py:71`), but usage entries store the count as `n` (`store.py:42`). Your pantry already has two usage entries, so it fails right away with `KeyError: 'qty'`. The server doesn't catch the error, so the browser gets no response and the stats area stays empty.

**6. Adding an item by barcode scan: you can't.** `python pantry.py scan` is listed in the README but was never written. Running it gives `invalid choice: 'scan'`. To add an item, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page. The web form has no unit field, so items added there are always `pcs`.

**7. Debug view of the raw data.** Visiting `GET /debug/dump` returns the whole JSON store, but only if the server was started with the `PANTRY_DEBUG` environment variable set (`server.py:43`). Otherwise it returns 404. Nothing on the page links to it, and there's no login. If someone starts the server with `PANTRY_DEBUG` set, anyone who can reach the server can open it. The server only listens on `127.0.0.1`, so that means people on the same machine.

**8. What changes the count when you press Use.** `store.use_item` (`store.py:36`). It loads the file, refuses to go below zero, decreases `qty` by `n`, logs `{id, n, date}`, and saves. The path is: `app.js` click handler → `Handler.do_POST` (`server.py:58`) → `store.use_item` → `store.save`.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the whole database file (`pantry.json`, or whatever `PANTRY_DB` points to) with `{"items": [], "used": []}`. That removes every item and the entire usage log, and there is no backup. It then adds a line saying `wiped` to `wipe.log` in the same folder. Without `--yes`, it prints a warning, exits 1, and changes nothing. Don't run it with `--yes` unless `PANTRY_DB` points to a scratch file.

The project's `FEATURES.md` describes all of this accurately. Its `AGENTS.md` says to run `python .features/features.py check --rerun` after you change anything.