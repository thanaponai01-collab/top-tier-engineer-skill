I read every file in the repo. I also ran the parts that could fail (shop, scan, export/import, stats, the debug route and wipe) against a temp copy of the database (`PANTRY_DB`). `fixture/pantry.json` is unchanged: its checksum was the same before and after, and the test server is shut down. The behaviour matches what `CLAUDE.md` says.

1. **Marking one unit used:** each item row has a **"Use 1"** button (`data-testid="use-btn"`). Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`web/static/app.js:23`). It returns 200 with the updated item, or 400 `{error}` if there isn't enough stock. I worked this out from the code and didn't click it in a browser, because `CLAUDE.md` says not to click it against the real file.

2. **Shopping list:** run `python pantry.py shop`. On your data it prints `- Eggs: buy 2 pcs` and `- Coffee: buy 1 bag`. An item goes on the list when its `qty` is below its `min`, and the amount to buy is `min - qty` (`store.py:57`). An item exactly at its minimum, like Olive oil at 1/1, is not listed. On the page, the same list comes from the **"Shopping list"** link, which calls `GET /api/shopping-list`.

3. **Keyboard shortcuts:** there are two (`app.js:47-55`):
   - **`/`** focuses the search box, unless you're already in it.
   - **Ctrl+Enter** submits the add form, from anywhere on the page.

4. **Moving the pantry with export and import:** no, this is broken. `python pantry.py export file.csv` works and writes `id,name,qty,min,unit`. But `python pantry.py import file.csv` reads a `quantity` column that doesn't exist and fails with `KeyError: 'quantity'` (`pantry.py:49`). Even once that's fixed, import always creates new items, so importing into a non-empty pantry duplicates entries. The CSV also leaves out the `used` history. Copying `pantry.json` to the other machine, or pointing `PANTRY_DB` at a copy of it, moves everything.

5. **"Usage stats" button:** no, it doesn't work. It calls `GET /api/stats`, and `store.stats` raises `KeyError: 'qty'` because it sums `u["qty"]` when the log entries use `n` (`store.py:71`). The server drops the connection without replying (curl exit code 52), so the button does nothing.

6. **Barcode scanning:** you can't. `python pantry.py scan` is listed in the README but doesn't exist. argparse rejects it with `invalid choice: 'scan'`, and there is no barcode or webcam code anywhere in the repo. The ways to add an item are `python pantry.py add NAME QTY [--min N] [--unit U]` or the Add form on the page. The form has no unit field, so items added there get `pcs`.

7. **Debug view:** yes, `GET /debug/dump` returns the whole database. It only works if the server was started with the `PANTRY_DEBUG` environment variable set (to anything non-empty). Otherwise it returns 404, which I confirmed. Nothing on the page links to it. Anyone who can reach the server while it runs in debug mode can open it, since there's no login. The server only listens on 127.0.0.1, though, so in practice that means anyone on the same machine.

8. **The function behind Use:** `store.use_item` (`store.py:36`). It checks there's enough stock, subtracts `n`, adds `{id, n, at}` to the `used` log, and saves. The server calls it from `Handler.do_POST` (`web/server.py:58`). The +1 button goes to `store.restock` instead, which adds to the count and doesn't log anything.

9. **What `wipe` deletes:** `python pantry.py wipe --yes` replaces the database with `{"items": [], "used": []}`, which removes every item and the whole usage history. It also adds a line `wiped` to `wipe.log` in the same folder as the database. There's no backup and no undo. Without `--yes` it only prints a warning and exits with code 1. It wipes whichever file `PANTRY_DB` points to, which is your real `pantry.json` if that variable isn't set.

`app.js` puts item names into the page without escaping them (`innerHTML`, `app.js:12-13`), so a name containing HTML would be rendered as HTML.