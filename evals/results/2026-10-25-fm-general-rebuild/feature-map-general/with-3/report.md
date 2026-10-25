I read all the code (`pantry.py`, `store.py`, `web/server.py`, `web/static/*`) and checked it against `FEATURES.md`. I also ran the shopping list, export/import and stats against a scratch copy (`PANTRY_DB` pointed at a temp file). Your real `pantry.json` was only read, never written.

1. **Use one unit on the web page:** the **"Use 1"** button in each item's row (`data-testid="use-btn"`). It sends `POST /api/items/{id}/use` with the body `{"n": 1}`. The server replies with the updated item, or a 400 error if there isn't enough left (`web/static/app.js:20-26`, `web/server.py:52-61`).

2. **Shopping list from the command line:** run `python pantry.py shop`. On your data it prints `- Eggs: buy 2 pcs` and `- Coffee: buy 1 bag`. Nobody adds items to it by hand. An item appears when its `qty` is below its `min`, and "buy" is `min - qty` (`store.py:56-58`). So using stock or raising an item's minimum is what puts it on the list. On the web it's the **"Shopping list"** link, which calls `GET /api/shopping-list`.

3. **Keyboard shortcuts** (`app.js:47-55`):
   - **`/`** jumps to the search box (unless you're already in it).
   - **`Ctrl+Enter`** submits the Add form.

4. **Moving your pantry with export/import: no.** `python pantry.py export out.csv` writes the columns `id,name,qty,min,unit`. But `import` reads a `quantity` column (`pantry.py:47`), so importing the file fails with `KeyError: 'quantity'`. I reproduced this. Even with that fixed, it wouldn't be a full move:
   - The CSV has no usage log.
   - Import adds rows as new items with new ids, so importing into a pantry that already has items creates duplicates.

   To move to another machine, copy `pantry.json` itself, or point `PANTRY_DB` at it.

5. **"Usage stats" button: no, it's broken.** It calls `GET /api/stats`, which runs `store.stats`. That function adds up `u["qty"]`, but the usage log stores entries as `{id, n, at}` (`store.py:71`). So as soon as anything has been used, it raises `KeyError: 'qty'` and the page gets a 500 error. Your pantry already has two logged uses, so it fails for you today. I reproduced the error.

6. **Barcode scanning: you can't. It doesn't exist.** The README lists `python pantry.py scan`, but `pantry.py` has no `scan` subcommand and there's no barcode or webcam code anywhere. Running it gives an argparse "invalid choice" error. The working ways to add an item are `python pantry.py add <name> <qty> [--min N] [--unit U]` or the **Add** form on the page.

7. **Debug view:** `GET /debug/dump` (`http://127.0.0.1:8040/debug/dump`) returns the whole data file. It only works if the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it returns 404. There's no login or authentication. If the server runs with `PANTRY_DEBUG` set, anyone who can reach the port can read the dump. The server only listens on `127.0.0.1`, so that means people on the same machine. The page has no link to it.

8. **What changes the stock count on Use:** `store.use_item` (`store.py:37-46`). It does `item["qty"] -= n`, adds an entry to the `used` log, and saves. The server route that calls it is in `web/server.py:58`.

9. **What `wipe` deletes:** `python pantry.py wipe --yes` replaces the data file with `{"items": [], "used": []}`. That removes every item and the whole usage log. It also adds a `wiped` line to `wipe.log` next to the data file. Without `--yes`, it just prints a warning and stops. It makes no backup.

Fixes worth making before other work: rename the import column to `qty`, sum `u["n"]` in `stats` (as written, its "uses" field actually counts units, not uses), and either remove `scan` from the README or build it.