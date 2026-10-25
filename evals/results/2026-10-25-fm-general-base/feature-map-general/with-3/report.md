I read all the code and docs. I also ran `stats`, `export`→`import` and `shop` against a temp copy (`PANTRY_DB` pointed at it). `pantry.json` is unchanged: I checked its checksum before and after.

**1. Marking one unit as used.** Each row in the item table has a **"Use 1"** button (`data-testid="use-btn"`, built in `web/static/app.js:14`). Clicking it sends `POST /api/items/<id>/use` with the JSON body `{"n": 1}` (`app.js:23`). The server answers with the updated item, or HTTP 400 if there's not enough stock. Then the table reloads.

**2. Shopping list from the command line.** Run `python pantry.py shop`. Your data printed `- Eggs: buy 2 pcs` and `- Coffee: buy 1 bag`. An item goes on the list only when its stock is below its minimum (`qty < min`, `store.py:57`), and the amount to buy is `min - qty`. Nothing adds an item to the list directly. It shows up when you `use` it below its minimum, or when you `add` it with `--min` higher than its quantity. To take it off, `restock` it. The web page has a "Shopping list" link (`GET /api/shopping-list`) that shows the same list.

**3. Keyboard shortcuts** (`app.js:47-55`). There are only two:
- `/` jumps to the search box, unless you're already in it.
- `Ctrl+Enter` submits the Add form.

**4. Moving the pantry with `export` then `import`: no.** `export` writes the columns `id,name,qty,min,unit`, but `import` reads a column called `quantity` (`pantry.py:49`). Importing a file you just exported fails with `KeyError: 'quantity'`; I reproduced this. Even with that fixed, it would only copy items: the usage log isn't exported, and imported items get new ids. For a full move, copy `pantry.json` itself, or point `PANTRY_DB` at it on the new machine.

**5. The "Usage stats" button: no.** It calls `GET /api/stats`. `store.stats` adds up `u["qty"]`, but each usage record is saved with the key `n` (`store.py:71` vs `:42`). So it fails with `KeyError: 'qty'`, which I reproduced on your data. The server drops the connection and the button shows nothing. It only works when nothing has been used yet, because then it returns zeros.

**6. Scanning a barcode: you can't.** The README lists `python pantry.py scan`, but there's no `scan` command; running it gives an argparse "invalid choice" error. To add an item, use `python pantry.py add <name> <qty> [--min N] [--unit U]` or the Add form on the page. The form always sets the unit to `pcs`.

**7. Debug view of the raw data.** There is one: `GET http://127.0.0.1:8040/debug/dump` returns the whole data file. It only works if the server was started with the `PANTRY_DEBUG` environment variable set; otherwise it returns 404. Nothing on the page links to it. There's no login, though: while debug mode is on, anything that can reach 127.0.0.1:8040 can read it. The server only listens on localhost, so other machines can't reach it.

**8. What changes the stock count when you press Use.** That's `store.use_item` (`store.py:36`). The path is click handler (`app.js:19`) → `Handler.do_POST` (`web/server.py:58`) → `use_item`. It refuses to go below zero, subtracts `n` from `qty`, adds `{id, n, at}` to the `used` log, and saves the file.

**9. What `wipe` deletes.** `python pantry.py wipe --yes` replaces the data file with `{"items": [], "used": []}`, which removes every item and the whole usage log. It also appends `wiped` to a `wipe.log` file next to the data file. Without `--yes` it only prints a warning and exits with code 1. It works on whatever file `PANTRY_DB` points to, so if `PANTRY_DB` isn't set, it empties your real `pantry.json`.

`FEATURES.md` agrees with the code on all of the above, so you can treat it as the up-to-date map.