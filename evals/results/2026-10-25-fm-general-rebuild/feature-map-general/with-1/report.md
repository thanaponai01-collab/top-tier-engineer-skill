I read all of the code and checked the answers by running them. `shop` and `scan` were the only commands I ran on your real `pantry.json`, and both just read it. Everything that writes (`export`/`import`, `use`, `wipe`, the web server) ran against a copy in a temp folder via `PANTRY_DB`. `pantry.json` is unchanged.

1. **Use one unit on the page:** each row has a **"Use 1"** button (`data-testid="use-btn"`, built in `web/static/app.js:15`). Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}`. On the copy, `POST /api/items/1/use` returned 200 and Rice went from 3 to 2 kg. If you try to use more than is left, you get a 400 with an error message.

2. **Shopping list from the command line:** run `python pantry.py shop`. An item goes on the list when its `qty` is below its `min`, and it says to buy `min - qty` (`store.py:54`). Your pantry currently prints `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. On the page, the **"Shopping list"** link calls `GET /api/shopping-list`.

3. **Keyboard shortcuts** (`app.js:47-56`):
   - **`/`** jumps to the search box.
   - **`Ctrl+Enter`** submits the Add form. It works wherever the cursor is on the page, not just inside the form.

4. **Export then import: no, it fails.** `python pantry.py export out.csv` writes the columns `id,name,qty,min,unit`, but `import` looks for a `quantity` column (`pantry.py:49`). I ran `import` on a file `export` had just written and it crashed with `KeyError: 'quantity'`. Note that `import` adds items with new ids; it doesn't replace what's there.

5. **"Usage stats" button: no, it doesn't work.** `store.stats` adds up `u["qty"]`, but usage entries are saved with the key `n` (`store.py:71` vs `store.py:42`). Your pantry has usage entries, so it raises `KeyError: 'qty'`. The server then closes the connection without sending any response. (FEATURES.md says it returns a 500, but that's not what happens.) On the page, the request fails and the stats area stays empty. There's no command-line version.

6. **Barcode scanning: it doesn't exist.** The README lists `python pantry.py scan`, but there's no such command and no barcode code anywhere. Running it gives `invalid choice: 'scan'` and exits with code 2. To add items, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page. Items added from the page are always `pcs`, because the form doesn't send a unit.

7. **Debug view:** `GET /debug/dump` returns the whole raw data file, but only if the server was started with the `PANTRY_DEBUG` environment variable set (`web/server.py:43`). Otherwise it returns 404, which I confirmed. There's no link to it on the page and no login. So a normal user can't reach it by default, but if debug is on, anyone who can reach the server can open it. The server only listens on 127.0.0.1, so that means people on the same machine.

8. **What changes the count when you press Use:** `store.use_item` (`store.py:36`). It does `item["qty"] -= n`, adds an entry to the usage log, and calls `save()`. The path is the button in `app.js` → `do_POST` in `web/server.py` → `store.use_item`. The command-line `use` calls the same function.

9. **`wipe`:** `python pantry.py wipe --yes` deletes every item and the whole usage log, leaving `{"items": [], "used": []}`. It also adds a line to `wipe.log` next to the data file. Without `--yes` it refuses and exits with code 1. Don't run it without `PANTRY_DB` pointing at a scratch file, or it empties your real `pantry.json`.

FEATURES.md and AGENTS.md describe the app accurately, apart from the stats detail in item 5. AGENTS.md also asks that after any change you run `python .features/features.py check --rerun` and then `prove --again`.