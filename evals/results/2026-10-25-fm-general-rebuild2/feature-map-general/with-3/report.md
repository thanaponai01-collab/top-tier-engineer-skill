I read all the code and checked it against `FEATURES.md`; they agree. I ran the read-only commands and the two failures (stats and import) against a scratch copy of your pantry using `PANTRY_DB`. `pantry.json` has the same checksum before and after, and I removed the `__pycache__` folders my runs created.

**1. Marking one unit as used.** Each item row on the page has a **"Use 1"** button (`data-testid="use-btn"`, `web/static/app.js:14`). Clicking it sends `POST /api/items/<id>/use` with the body `{"n": 1}` (`app.js:23`). The server returns the updated item, or HTTP 400 if there isn't enough left (for example `only 0 bag of Coffee left`). The page ignores that error and just refreshes the list. The "+1" button next to it sends the same request to `/restock`.

**2. Shopping list from the command line.** Run `python pantry.py shop`. An item goes on the list when its `qty` is below its `min`, and the amount to buy is `min − qty` (`store.py:57`). Right now that gives `Eggs: buy 2 pcs` and `Coffee: buy 1 bag`. You can also see these items with `python pantry.py list --low`. On the web page, click the **"Shopping list"** link (it calls `GET /api/shopping-list`).

**3. Keyboard shortcuts** (`app.js:47-55`):
- **`/`** puts the cursor in the search box, unless it's already there.
- **`Ctrl+Enter`** submits the Add form. The form has no unit field, so items added on the web always get the unit `pcs`.

**4. Moving with `export` then `import`: no.** `python pantry.py export file.csv` works, but `python pantry.py import file.csv` fails with `KeyError: 'quantity'`. Export writes a column called `qty`, but import reads `quantity` (`pantry.py:49`). Even with that fixed, import *adds* items to whatever pantry is already there; it doesn't replace it. On a machine that already has items you'd get duplicates.

**5. "Usage stats" button: no.** It calls `GET /api/stats`, which crashes with `KeyError: 'qty'`. `stats()` adds up `u["qty"]` (`store.py:71`), but `use_item` records the amount under `"n"`. It only works while the usage log is empty, and yours has 2 entries. Because the server crashes rather than returning an error, the stats area on the page shows nothing useful.

**6. Adding by barcode scan: you can't.** `python pantry.py scan` is in the README but was never built: `invalid choice: 'scan'`. The only ways to add an item are `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page.

**7. Debug view of the raw data:** `GET /debug/dump` returns the whole database as JSON. It only works if the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it returns 404 (`web/server.py:43`). It has no login, so anyone who can open the page can reach it when the flag is on. The server only listens on 127.0.0.1, so that means people on this machine.

**8. What changes the count when you press Use:** `store.use_item` (`store.py:36`). The request goes from the Use button through `Handler.do_POST` (`web/server.py:58`) to `use_item`. That function lowers `qty`, adds `{id, n, at}` to the `used` log, and saves through `store.save`.

**9. What `wipe` deletes:** `python pantry.py wipe --yes` deletes every item and the whole usage log, leaving `{"items": [], "used": []}`. It also appends a line to `wipe.log` next to the database. There's no backup and no undo. Without `--yes` it refuses and exits with code 1. To try it, set `PANTRY_DB` to a scratch file first.

`AGENTS.md` asks that after any change you run `python .features/features.py check --rerun`, then `python .features/features.py prove --again`, to keep `FEATURES.md` accurate.