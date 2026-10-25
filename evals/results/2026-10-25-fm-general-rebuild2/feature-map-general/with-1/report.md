I read the code and `FEATURES.md`, then ran `python .features/features.py check --rerun`. That command replays every recorded run in a throwaway copy, and all of them gave the same result as before. `pantry.json` has the same hash before and after, so it wasn't touched.

1. **Marking one unit as used:** each item row has a **"Use 1"** button (`[data-testid=use-btn]`). The rows are built in `web/static/app.js:14`. Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`app.js:23`). The server answers 200 with the updated item, or 400 if the item doesn't exist or there isn't enough left. The **"+1"** button next to it sends the same kind of request to `/restock`.

2. **Shopping list:** run `python pantry.py shop`. On the web page, the **"Shopping list"** link calls `GET /api/shopping-list`. An item goes on the list when its quantity is below its minimum (`qty < min`), and the list says to buy `min - qty` (`store.py:55-57`). So an item lands there either by using it below its `--min`, or by adding it with a `--min` higher than its quantity. In your current pantry, Eggs (buy 2) and Coffee (buy 1) are on the list.

3. **Keyboard shortcuts:** there are only two, both in `app.js:47-55`:
   - `/` jumps to the search box.
   - `Ctrl+Enter` submits the add form.

4. **Moving the pantry with `export` then `import`:** no, it doesn't work.
   - `python pantry.py export out.csv` works and writes the columns `id,name,qty,min,unit`.
   - `python pantry.py import out.csv` crashes with `KeyError: 'quantity'`, because `pantry.py:49` reads a `quantity` column that export never writes. The recorded run fails, and it failed again just now.
   - Even with that fixed, import doesn't restore anything. It adds rows through `add_item`, so items get new ids, nothing is merged with what's already there, and the usage log isn't carried over. Copying `pantry.json` (or pointing `PANTRY_DB` at the copy) is the only reliable way to move it.

5. **"Usage stats" button:** no, it doesn't work.
   - The button (`[data-testid=stats-btn]`) calls `GET /api/stats`.
   - `store.stats` (`store.py:71`) adds up `u["qty"]`, but usage entries are stored as `{"id", "n", "at"}`, so it raises `KeyError: 'qty'` and the server drops the connection.
   - Your real pantry already has 2 usage entries, so the button fails on your data too. It only "works" when nothing has been used yet, and then it shows `{"uses": 0, "per_day": 0.0}`.

6. **Barcode scanning:** you can't, because it doesn't exist. `python pantry.py scan` appears in the README, but `pantry.py` has no `scan` subcommand (argparse rejects it as an invalid choice) and there's no camera or barcode code anywhere. To add items, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the **Add** form on the page.

7. **Debug view of raw data:** `GET /debug/dump` (`web/server.py:43`) returns all of `pantry.json` (items and usage log). It only answers when the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it's a 404. Nothing on the page links to it and there's no login, so anyone who can reach the server could open that URL while the variable is set. The server only listens on `127.0.0.1`, which in practice limits that to people on your machine.

8. **What changes the count when you press Use:** `store.use_item` (`store.py:36-44`). The route in `web/server.py:58` calls it. It reloads the file, refuses if `qty < n`, subtracts `n`, adds `{id, n, at: today}` to the usage log, and saves.

9. **What `wipe` deletes:** with `python pantry.py wipe --yes` (it refuses without `--yes`), it replaces the whole database with `{"items": [], "used": []}`. That removes every item and the entire usage log. There's no backup. The only other thing it does is add a line `wiped` to a `wipe.log` file next to the database. It deletes no other files.