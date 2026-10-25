I read the code and checked each answer. Everything I ran used a scratch copy of the pantry (`PANTRY_DB` pointed at a temp file, server on port 8763). `pantry.json` has the same checksum before and after.

**1. Marking one unit used (web).** Each row in the table has a **"Use 1"** button (`data-testid="use-btn"`). It sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`web/static/app.js:21-26`). It returns the updated item; I got `{"id": 1, "name": "Rice", "qty": 2, ...}`. Asking for more than is left gets a 400 with `only N <unit> of <name> left`.

**2. Shopping list from the CLI.** Run `python pantry.py shop`. On your data it prints `- Eggs: buy 2 pcs` and `- Coffee: buy 1 bag`. Nothing adds an item to the list directly. An item appears when its `qty` drops below its `min`, and the "buy" number is `min - qty` (`store.py:50-52`). So it gets there by using it (`use`, the Use 1 button) or by adding it with `--min` above its quantity. The web page shows the same list from the **"Shopping list"** link, which calls `GET /api/shopping-list`.

**3. Keyboard shortcuts.** There are two (`web/static/app.js:49-57`):
- **`/`** puts the cursor in the search box, unless you're already typing there.
- **`Ctrl+Enter`** submits the Add form from anywhere on the page. With an empty form it adds an item with no name.

**4. Moving the pantry with export/import: no.** `export` writes the columns `id,name,qty,min,unit`, but `import` reads a `quantity` column (`pantry.py:57`). It stops with `KeyError: 'quantity'`, which I confirmed. Even with that fixed, `import` adds every row as a new item with a new id, and the usage log isn't exported at all. To move it today, copy `pantry.json` itself.

**5. "Usage stats" button: no, it shows nothing.** `store.stats` adds up `u["qty"]`, but usage log entries store the amount as `n` (`store.py:71`). It raises `KeyError: 'qty'` whenever anything has been used, as it has in your pantry. FEATURES.md says this gives a 500. In my test the server actually dropped the connection without any response, so the page's fetch just fails.

**6. Scanning a barcode: you can't.** The README lists `python pantry.py scan`, but that command doesn't exist. argparse rejects it with `invalid choice: 'scan'`, and there is no barcode or webcam code anywhere in the app.

**7. Debug view.** `GET /debug/dump` returns the whole data file. It only works if the server was started with the `PANTRY_DEBUG` environment variable set (for example `PANTRY_DEBUG=1 python pantry.py serve`, then http://127.0.0.1:8040/debug/dump). Otherwise it's a 404, which is what I got. It has no login and nothing on the page links to it. Anyone who can reach the server can open it while the flag is on. The server only listens on 127.0.0.1, so that means people on the same machine.

**8. What changes the count on Use.** `store.use_item` (`store.py:35-44`). The request goes from the click handler in `app.js` to `Handler.do_POST` in `web/server.py` (matched by `ITEM_ACTION`) and then to `store.use_item`. That function lowers `qty`, adds `{id, n, at}` to the `used` log, and writes the file with `store.save`.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the data file's contents with `{"items": [], "used": []}`, so every item and the whole usage log are gone. It doesn't delete the file itself. It also adds a line `wiped` to `wipe.log` next to the data file. There's no backup. Without `--yes` it refuses and exits 1.

The repo's `FEATURES.md` is accurate on all of these except the stats failure (it says 500; I saw no response at all). `AGENTS.md` asks that commands that write data be run only against a copy, never the real `pantry.json`.