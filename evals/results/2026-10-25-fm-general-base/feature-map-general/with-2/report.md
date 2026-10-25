I answered these by reading the code (`pantry.py`, `store.py`, `web/server.py`, `web/static/*`) and checking it against `FEATURES.md`; the two agree. I also ran the read-only commands, plus `export`/`import` and the stats function on a temporary copy of your pantry (`PANTRY_DB=<temp>`). `pantry.json` has the same checksum before and after.

**1. Marking one unit as used:** each row in the table has a **"Use 1"** button (`data-testid="use-btn"`, built in `web/static/app.js:14`). Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}`. If there isn't enough stock the server answers 400 with an error, but the page doesn't show it; it just reloads the list.

**2. Shopping list from the command line:** run `python pantry.py shop`. On your data it currently prints `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. An item goes on the list when its `qty` falls **below its `min`**, and it says to buy `min - qty` (`store.py:54`). Nothing adds items to the list by hand; it's always worked out from stock. You set the minimum with `add <name> <qty> --min N`, and using items lowers the stock. On the web, the "Shopping list" link fetches `GET /api/shopping-list`.

**3. Keyboard shortcuts** (`app.js:47-56`):
- `/` puts the cursor in the search box, unless it's already there.
- `Ctrl+Enter` submits the Add form. This works from anywhere on the page, even when the cursor is in the search box.

**4. Moving the pantry with export then import: no, not as it stands.** `python pantry.py export file.csv` works, but `python pantry.py import file.csv` fails with `KeyError: 'quantity'` (I reproduced this). Export writes a `qty` column while import reads `quantity` (`pantry.py:48`). Also, neither one carries the usage log. Until that's fixed, copy `pantry.json` itself, or point `PANTRY_DB` at it on the other machine.

**5. "Usage stats" button: no.** It calls `GET /api/stats`, and `store.stats()` adds up `u["qty"]` when log entries actually store `n` (`store.py:71`). With your data that's a `KeyError: 'qty'`, so the request gets no response and the button shows nothing. It only "works" when the usage log is empty.

**6. Scanning a barcode: you can't.** The README lists `python pantry.py scan`, but that command doesn't exist. Running it gives `invalid choice: 'scan'`. To add an item, use `python pantry.py add <name> <qty> [--min N] [--unit U]`, or the Add form on the page.

**7. Debug view: yes, `GET /debug/dump`** (http://127.0.0.1:8040/debug/dump). It returns all of `pantry.json`, but only if the server was started with the `PANTRY_DEBUG` environment variable set. Otherwise it returns 404. Nothing on the page links to it. There's no login or other check, so when it's turned on, anyone who can reach the server can read it. The server listens only on 127.0.0.1, which limits that to your own machine.

**8. What changes the count when you press Use:** `store.use_item()` (`store.py:36`). It's called from `Handler.do_POST` in `web/server.py:57`. It checks there's enough stock, does `qty -= n`, adds `{id, n, at}` to the `used` log, and saves.

**9. What `wipe` deletes:** `python pantry.py wipe --yes` empties every item and the whole usage log, leaving `pantry.json` as `{"items": [], "used": []}`. It also appends the line `wiped` to `wipe.log` in the same folder. Without `--yes` it prints a warning, exits 1 and changes nothing. There's no backup or undo. I didn't run it.