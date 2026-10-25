I read every file in `fixture/` and ran the risky parts against a temp copy (`PANTRY_DB` pointed at it). `pantry.json` was not touched, and `cmp` confirmed it's unchanged afterwards. The repo's `AGENTS.md` matches the code.

**1. Using one unit on the web page.** Each row has a **"Use 1"** button (`data-testid="use-btn"`, `data-id` = the item id). Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`web/static/app.js:19-25`). It gets back 200 with the updated item, or 400 `{"error": ...}` for an unknown id or when stock is too low. The page then reloads the list. The "+1" button next to it sends the same request to `/restock`.

**2. Shopping list from the command line.** Run `python pantry.py shop`. Your real data prints `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. An item goes on the list when its `qty` is below its `min`, and the amount to buy is `min - qty` (`store.py:55-57`). An item exactly at its minimum, like Olive oil at 1/1, is left off. You can also get the list from `GET /api/shopping-list`, or the "Shopping list" link on the page.

**3. Keyboard shortcuts** (`app.js:47-55`), and there are only these two:
- `/` moves focus to the search box (unless it's already there).
- `Ctrl+Enter` submits the add-item form.

**4. Moving your pantry with export/import: no.** `export` writes the columns `id,name,qty,min,unit`, but `import` looks for a `quantity` column (`pantry.py:49`). I tested it: importing an export fails with `KeyError: 'quantity'` before adding anything. Even if that were fixed, CSV only carries items, so the usage log would be lost and ids would be reassigned. To move everything, copy `pantry.json` itself (or point `PANTRY_DB` at the copy).

**5. The "Usage stats" button: no, it's broken.** It calls `GET /api/stats`, which runs `store.stats()`. That function adds up `u["qty"]`, but usage entries store the count as `n` (`store.py:71`). It crashes with `KeyError: 'qty'` (confirmed), the server never sends a response, and the stats box stays empty.

**6. Adding by barcode: you can't.** The README advertises `python pantry.py scan`, but that command doesn't exist. It fails with `invalid choice: 'scan'`, and there's no webcam or barcode code anywhere. To add an item, run `python pantry.py add NAME QTY [--min N] [--unit U]` or use the Add form on the page.

**7. Debug view of the raw data.** `GET http://127.0.0.1:8040/debug/dump` returns the whole database, but only if the server was started with the `PANTRY_DEBUG` environment variable set. Otherwise it returns 404 (`web/server.py:43`). Nothing on the page links to it. If it's on, there's no login, so anyone who can reach the server can open it. The server only listens on `127.0.0.1`, which in practice means anyone on the same machine.

**8. The function that changes the stock on Use.** That's `store.use_item()` at `store.py:36-44`. It checks there's enough stock, subtracts `n` from `qty`, adds an entry `{id, n, at: today}` to the usage log, and saves the whole file. The server's `do_POST` (`web/server.py:58`) is what calls it.

**9. What `wipe` deletes.** Run alone, `python pantry.py wipe` deletes nothing: it prints a warning and exits with code 1 (confirmed). `wipe --yes` replaces the database with `{"items": [], "used": []}`, which erases every item and the whole usage log. It makes no backup. It also appends a line to `wipe.log` in the same folder as the database. It doesn't delete the file itself.

Two other problems I noticed while reading:
- Adding an item with a non-number `qty` or `min` crashes the request. This happens, for example, if you clear the `min` field on the form, and nothing gets saved.
- The page inserts item names into the HTML without escaping them.