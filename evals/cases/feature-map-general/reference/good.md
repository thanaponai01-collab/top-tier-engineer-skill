From FEATURES.md, re-checked by running each:

1. The per-row **Use 1** button, `[data-testid=use-btn]`, sends `POST /api/items/<id>/use` with `{"n": 1}`.
2. `python pantry.py shop`. An item is listed when its qty is below its min; it says to buy min - qty.
3. `/` focuses the search box; Ctrl+Enter submits the add form.
4. No. `export` writes a `qty` column but `import` reads `quantity`, so importing an export fails with KeyError: 'quantity'.
5. No. It calls `GET /api/stats`, and `store.stats` reads `u["qty"]` from usage entries that store `n`: KeyError: 'qty'.
6. You can't: there is no `scan` command (argparse says invalid choice). The README is wrong.
7. `GET /debug/dump` returns the raw JSON, but only when `PANTRY_DEBUG` is set; otherwise 404.
8. `store.use_item` in store.py, called from `do_POST` in web/server.py.
9. `wipe --yes` empties every item and the usage log in pantry.json; without --yes it refuses.

I didn't touch pantry.json.
