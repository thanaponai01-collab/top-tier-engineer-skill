README updated with where the alert lands (alerts.log) and when it fires.

But it does not fire on a sale any more. The project's check (`python .features/features.py check
--rerun` / `verify.py run`) went red: `shop.py sell widget 9` wrote no alert. shop.py now imports
app.handlers only inside cmd_restock, so `sell` never loads the handlers: no alert, no audit line,
no reorder note. Restock still works. Moving the import back to the top of shop.py fixes it.
