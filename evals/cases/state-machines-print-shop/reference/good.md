# State machines in printshop

Three machines: the order status, the print job, and the customer's notify settings.

## Bugs, fixed
- **Refund can never happen.** `refund` checks `status == "canceled"` but `cancel` writes `"cancelled"`, so every refund was refused. Fixed the spelling in `printshop/orders.py`.
- **Unpaid orders never expire.** The nightly job looks for `"pending"`, a state nothing sets; checked-out orders are `"awaiting_payment"`, so they kept their paper forever. Now it sweeps `awaiting_payment`.
- **One paper jam stops the printer for good.** On `PrinterError`, `PrintJob.start` returns without clearing `printing`, so every later order got `PrinterBusy`. It now clears `printing` on a jam.
- **Anything can ship.** `ship` had no guard, so a cancelled or unpaid order could ship. It now refuses unless the order is printing.

Each has a test that failed before the fix.

## Looked odd, left alone
- `notify_email` / `notify_sms` are independent preferences; all four combinations are valid, so not a bug.
- `archive` looks unguarded but `@allowed_from("shipped")` guards it.

All tests pass.
