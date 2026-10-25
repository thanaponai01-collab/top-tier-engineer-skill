I added a short "Low-stock alert" section to `README.md`. It says alerts go to `alerts.log` in the folder you run `shop.py` from, and shows a sample line (`… LOW STOCK widget: 4 left`). It also says when the alert fires: once, when a sale takes a shelf from 5 or more to below 5. It can fire again only after a restock brings the shelf back to 5 or more.

**Don't send this to the floor team yet: the alert never fires on a sale.** In `shop.py`, only `cmd_restock` loads the handlers (`import app.handlers`). `cmd_sell` doesn't, so a sale tells no handler about the change. I tested this on a copy of the shop: I sold gadget from 40 down to 1 and no `alerts.log` was created. The same problem hits the audit trail and the reorder reminder, so sales currently leave no audit record and trigger no reorder.

The fix is one line: move `import app.handlers` to the top of `shop.py`, or into `cmd_sell` as well. You only asked for the README, so I haven't changed the code — should I make that fix?

Also, `app/bus.py` silently ignores any error inside a handler. If `alerts.log` can't be written (for example, because of folder permissions), alerts just stop and nothing reports it.