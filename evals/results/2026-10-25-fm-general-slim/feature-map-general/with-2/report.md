I read all the source files and ran the shopping list, export → import, and stats against a scratch copy (`PANTRY_DB` set to a temp file). `pantry.json` was not touched; its hash is the same before and after.

**1. Marking one unit as used (web).** Each item row has a **"Use 1"** button (`data-testid="use-btn"`), built in `web/static/app.js:14`. Clicking it sends `POST /api/items/<id>/use` with the JSON body `{"n": 1}` (`app.js:24`). The server matches that path with `ITEM_ACTION` (`web/server.py:9`). The "+1" button next to it does the same thing but sends `/restock`.

**2. Shopping list from the command line.** Run `python pantry.py shop`. On your pantry it prints `- Eggs: buy 2 pcs` and `- Coffee: buy 1 bag`. An item goes on the list when its `qty` is below its `min`, and the amount to buy is `min - qty` (`store.py:55`). You can't add things to the list by hand; you control it by setting `--min` on `add`. On the web page it's the **"Shopping list"** link, which calls `GET /api/shopping-list`.

**3. Keyboard shortcuts** (`app.js:47-55`). There are only two:
- `/` puts the cursor in the search box, unless you're already typing in it.
- `Ctrl+Enter` submits the Add form.

**4. Moving the pantry with export/import.** No, it doesn't work. `python pantry.py export out.csv` writes the columns `id,name,qty,min,unit`, but `import` reads a `quantity` column (`pantry.py:50`). I tried it and it fails with `KeyError: 'quantity'`. Even with that fixed, two things would still be lost:
- **Usage log:** export only writes items, so the log never leaves the machine.
- **Item ids:** import adds each row as a new item with a new id, so it duplicates items rather than restoring them.

To move the pantry today, copy `pantry.json` itself, or point `PANTRY_DB` at the copy.

**5. "Usage stats" button.** It's broken. The button calls `GET /api/stats`, and `store.stats` adds up `u["qty"]`, but the usage log stores `n` (`store.py:69` compared with `store.py:42`). I confirmed it raises `KeyError: 'qty'`, so the server returns a 500 and the page shows nothing useful. There is no command-line version of stats.

**6. Barcode scanning.** You can't. `python pantry.py scan` appears only in the README. `pantry.py` has no `scan` subcommand, so running it gives an argparse "invalid choice" error. The only ways to add items are `python pantry.py add <name> <qty> [--min N] [--unit U]` and the Add form on the page. Items added through the form always get the unit `pcs`, because the form sends no unit.

**7. Debug view of the raw data.** There is one: `GET /debug/dump` returns the whole database as JSON (`server.py:42`). It only answers when the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it returns 404. Nothing on the page links to it.
- **Default setup:** a normal user can't reach it.
- **With `PANTRY_DEBUG` set:** anyone who can reach the server can read it, because there is no authentication. The server only listens on `127.0.0.1`, so that means only local users.

**8. What changes the stock when you press Use.** `store.use_item` (`store.py:36`) does it. The path is: click handler in `app.js`, then `Handler.do_POST` in `web/server.py`, then `store.use_item`. That function reloads the file, refuses with a 400 if there isn't enough stock, runs `item["qty"] -= n`, adds `{id, n, at: today}` to `used`, and saves. The command-line `use` command calls the same function.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the database with `{"items": [], "used": []}`, which removes every item and the whole usage log (`pantry.py:59`). Without `--yes` it refuses. It also appends `wiped` to a `wipe.log` file next to the database. It does not delete the file itself or keep any backup. If `PANTRY_DB` isn't set, it wipes your real `pantry.json`.

FEATURES.md already describes most of this accurately, including that stats and import fail and that `scan` doesn't exist. Two notes in it are worth knowing: its tests of the page went through the requests the buttons send rather than real browser clicks, and `AGENTS.md` asks that anything which writes data be run against a copy.