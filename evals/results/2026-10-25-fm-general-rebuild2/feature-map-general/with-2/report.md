I read all the code and ran `python .features/features.py check --rerun`. That command replays the recorded runs, and anything that writes runs on a throwaway copy. All 25 entry points still match the code, and every run gave the same result as when it was recorded. `pantry.json` is byte-identical before and after (same SHA-1), and I deleted the `__pycache__` folder the run created.

**1. Using one unit on the web page.** Each row has a **"Use 1"** button (`data-testid="use-btn"`, built in `web/static/app.js:14`). Clicking it sends `POST /api/items/<id>/use` with body `{"n": 1}` (`app.js:23`). The server replies 200 with the updated item, or 400 if there isn't enough stock or the item doesn't exist. Then the page reloads the table. The "+1" button next to it sends `POST /api/items/<id>/restock` the same way.

**2. Shopping list.** Run `python pantry.py shop`, which prints lines like `- Eggs: buy 2 pcs`. On the page, the **"Shopping list"** link calls `GET /api/shopping-list`. You don't add items to the list by hand. An item appears when its stock is below its minimum (`qty < min`), and the "buy" amount is `min - qty` (`store.py:57`). You set the minimum with `add ... --min N` or the third field of the web form, and stock falls when you use the item.

**3. Keyboard shortcuts** (`app.js:47-55`):
- **`/`** moves the cursor to the search box. It doesn't search anything by itself. It works from any field except the search box, so you can't type a `/` into the Add form's name field.
- **`Ctrl+Enter`** submits the Add form from anywhere on the page.

**4. Moving your pantry with export and import: no.** `python pantry.py export out.csv` works and writes the columns `id,name,qty,min,unit`. But `python pantry.py import out.csv` crashes with `KeyError: 'quantity'`, because `cmd_import` reads a `quantity` column (`pantry.py:49`). The recorded run fails the same way today. Even once that's fixed, the CSV has no usage log, and imported items get new ids instead of their old ones. For now, copying `pantry.json` (or pointing `PANTRY_DB` at a copy) is the way to move it.

**5. "Usage stats" button: no.** The button (`data-testid="stats-btn"`) calls `GET /api/stats`. `store.stats` adds up `u["qty"]`, but each usage-log entry stores its amount as `n` (`store.py:42` vs `store.py:71`). The result is a `KeyError` and a dropped connection, and the button shows nothing. Your pantry already has two logged uses, so it will fail for you. It only works on a pantry with no uses at all, where it returns zeros.

**6. Barcode scanning: you can't.** The README lists `python pantry.py scan`, but that subcommand doesn't exist, so argparse will reject it. No code anywhere handles a webcam or barcodes. To add items, use `python pantry.py add NAME QTY [--min N] [--unit U]` or the web form. The web form sends no unit, so items added there always get `pcs`.

**7. Debug view of the raw data.** `GET /debug/dump` returns the whole `pantry.json` (`web/server.py:43`), but only if the server was started with the `PANTRY_DEBUG` environment variable set. Otherwise it returns 404. Nothing on the page links to it. When it is enabled there's no login check, so anyone who can reach the server can open it. The server only listens on `127.0.0.1`, which in practice means anyone on your own machine.

**8. Which function changes the count when you press Use:** `store.use_item` (`store.py:36`). It checks there's enough stock, subtracts `n`, adds `{id, n, at: today}` to the usage log, and saves. It's called from `Handler.do_POST` in `web/server.py:58`.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the database with `{"items": [], "used": []}`, which erases every item and the whole usage log. It doesn't delete the file itself, keeps no backup, and adds a `wiped` line to `wipe.log` next to the database. Without `--yes` it only prints a warning and exits with code 1. By default the database is your real `pantry.json`, so only try it with `PANTRY_DB` pointing at a copy.

One small thing in `FEATURES.md` is slightly off: the Use item trace lists the route as `/api/items`, but the button actually calls `/api/items/<id>/use`.