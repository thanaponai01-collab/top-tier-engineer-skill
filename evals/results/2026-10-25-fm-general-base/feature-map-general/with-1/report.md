I read the code and checked FEATURES.md against it. I ran the read-only commands and the two that FEATURES.md lists as failing (stats, import), but only on throwaway copies. `pantry.json` has the same checksum before and after (`95b2009b…`).

**1. Marking one unit as used:** each row's **"Use 1"** button (`data-testid="use-btn"`, built in `web/static/app.js`). It sends `POST /api/items/<id>/use` with the body `{"n": 1}`. The page then reloads the list with `GET /api/items`. If the stock is already 0, the server returns a 400 error, but the page doesn't show it.

**2. Shopping list:** run `python pantry.py shop` (the web version is `GET /api/shopping-list`, or the "Shopping list" link). You can't add things to it directly. An item shows up when its `qty` drops below its `min`, and the amount to buy is `min − qty`. So an item gets on the list when you use it below its minimum (`python pantry.py use <id> [n]` or the Use button), or when you add it with a low quantity (`add <name> <qty> --min N`). Right now the list shows "Eggs: buy 2 pcs" and "Coffee: buy 1 bag".

**3. Keyboard shortcuts** (`app.js`):
- `/` jumps to the search box.
- `Ctrl+Enter` submits the Add form.

There are no others.

**4. Moving your pantry with export/import:** not yet, because import is broken. `python pantry.py export out.csv` works and writes the columns `id,name,qty,min,unit`. But `python pantry.py import out.csv` fails with `KeyError: 'quantity'`: `cmd_import` reads `row["quantity"]`, while export writes `qty`. I reproduced this on a scratch copy. Even once that's fixed:
- Import adds items and gives them new ids. It doesn't replace what's there.
- The usage log (`used`) is never exported.

For now, the simplest way to move your pantry is to copy `pantry.json` to the other machine.

**5. "Usage stats" button:** no. `GET /api/stats` crashes and the server drops the connection without a response. I reproduced this with `python tools/hit.py GET /api/stats`. The cause is that `store.stats` adds up `u["qty"]`, but log entries store the count as `n`. On the page, clicking the button shows nothing.

**6. Scanning a barcode:** you can't. The README mentions `python pantry.py scan`, but that command doesn't exist. Running it gives `invalid choice: 'scan'`. To add items, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page. Items added through the web form always get the unit `pcs`.

**7. Debug view of the raw data:** `GET /debug/dump` returns the whole file. It only works if the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it returns 404, which I confirmed. A normal user can't reach it in a default setup. If someone does start it with `PANTRY_DEBUG`, anyone who can reach the server can open it, since there's no login. The server only listens on `127.0.0.1`, so that means anyone on that machine.

**8. Function that changes the stock count on Use:** `store.use_item` in `store.py`. It checks there's enough stock, lowers `qty`, adds `{id, n, at}` to the usage log, and saves the file. The path there is: the click handler in `app.js` → `Handler.do_POST` in `web/server.py` (which matches the URL) → `store.use_item`.

**9. What `wipe` deletes:** `python pantry.py wipe --yes` replaces the data file with `{"items": [], "used": []}`. That removes every item and the whole usage log. It also adds a line saying `wiped` to `wipe.log` next to the file. It has no undo and makes no backup. Without `--yes`, it prints a warning, exits with code 1, and changes nothing. It acts on whatever file `PANTRY_DB` points to, and on your real `pantry.json` if that's unset.

Two small doc errors to know about:
- FEATURES.md calls the helper `.features/drive/hit.py`, but it's actually at `tools/hit.py`.
- In Git Bash, you need `MSYS_NO_PATHCONV=1` before running `hit.py`. Otherwise Git Bash rewrites `/api/...` into a Windows path.