I added a short "Low-stock alert" section to `README.md`. But the alert can't fire on a sale right now, which is when stock actually drops.

**What the README now says:**
- **Where it lands:** a line is added to `alerts.log`, e.g. `2026-10-25T14:02:11 LOW STOCK widget: 4 left`.
- **When it fires:** when a shelf goes from 5 or more to under 5 (`LOW_STOCK_THRESHOLD` in `app/config.py`). It fires once when the count crosses that line, not again on every sale below 5. It can fire again after a restock brings the count back to 5 or more.

**The problem:** the alert handlers are only loaded inside `cmd_restock` in `shop.py`. `sell` never loads them. Since a restock only adds stock, it can never cross the threshold downward, so the alert never fires in practice. I checked this on a copy of the inventory: `sell widget 11` left 1 widget, and no `alerts.log` was created. The same bug means sales also don't write to `audit.log` or `reorder.txt`, even though the README already said every stock change does.

So the README isn't misleading for now, I added a "Known issue" line about this. The fix is one line: move `import app.handlers` to the top of `shop.py`, or into `cmd_sell` too. Once that's done, the "Known issue" line can be deleted. Want me to make that fix?