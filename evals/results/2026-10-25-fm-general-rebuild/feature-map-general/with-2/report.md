I read all of the code and ran the CLI on a scratch copy of your pantry. `pantry.json` has the same checksum before and after; the only thing added to the folder was Python's `__pycache__/`.

**1. Marking one unit as used (web).** Each row has a **"Use 1"** button (`data-testid="use-btn"`), built in `web/static/app.js:14`. Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`app.js:20-26`). The server matches that path with `ITEM_ACTION` (`web/server.py:9`) and returns the updated item, or a 400 if there's too little stock. The "+1" button next to it is restock, not use.

**2. Shopping list from the command line.** Run `python pantry.py shop`. An item goes on the list when its quantity is **strictly below** its minimum (`store.py:56`). An item sitting exactly at its minimum, like Olive oil at 1/1, is not listed. The list shows how many to buy to get back to the minimum. Right now it shows Eggs (buy 2) and Coffee (buy 1). On the web, the same list is behind the "Shopping list" link, which calls `GET /api/shopping-list`.

**3. Keyboard shortcuts** (`app.js:47-55`):
- **`/`** puts the cursor in the search box. It works from any other field too, so you can't type a `/` into the item-name box.
- **`Ctrl+Enter`** submits the add-item form.

**4. Moving the pantry with export then import: no, it fails.** `python pantry.py export out.csv` writes the columns `id,name,qty,min,unit`, but `import` reads a `quantity` column (`pantry.py:49`). I tried it and import stopped with `KeyError: 'quantity'` on the first row, so nothing was added. Two more limits even once that's fixed:
- Import only adds items, so the target pantry's existing items stay.
- Neither command carries the usage log.

Copying `pantry.json` itself, or pointing `PANTRY_DB` at it, does move everything.

**5. The "Usage stats" button: no, it doesn't work.** It calls `GET /api/stats`, which runs `store.stats`. That function adds up `u["qty"]`, but the usage log stores `n` (`store.py:71` vs `store.py:42`). With your data it raises `KeyError: 'qty'`, so the server returns an error and the button shows nothing useful. If no use has been logged yet, it works and returns 0.

**6. Adding an item by barcode scan: you can't.** The README advertises `python pantry.py scan`, but that command doesn't exist. Running it gives `invalid choice: 'scan'`. To add an item, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page.

**7. Debug view of the raw data.** `GET /debug/dump` returns the whole database (items and usage log), but only when the server was started with the `PANTRY_DEBUG` environment variable set (`server.py:43`). Otherwise it returns a 404. Nothing on the page links to it. The server only listens on 127.0.0.1 and has no login, so anyone on that machine can open it while debug mode is on. Other machines can't reach it.

**8. The function that changes the stock count on Use:** `store.use_item` (`store.py:36`). It reloads the file, refuses to go below 0, subtracts `n`, logs `{id, n, at: today}`, and saves.

**9. What `wipe` deletes:** `python pantry.py wipe --yes` replaces the database with `{"items": [], "used": []}`, which deletes every item and the whole usage log. It also adds a "wiped" line to `wipe.log` in the database's folder. Without `--yes` it only prints a warning. It deletes nothing else, and it makes no backup.

I tested 2, 4, 5 and 6 by running them on the copy. Answers 1, 3, 7, 8 and 9 come from reading the code; I didn't start the web server or run `wipe`.