I found four state machines in the app and fixed five bugs in them. All 11 tests pass: the 6 that were already there and 5 new ones, one for each bug.

## The state machines

**1. Order status** (`printshop/orders.py`, plus `jobs.py` and `guards.py`)
`draft → awaiting_payment → paid → printing → shipped → archived`. An order can also go to `cancelled` from `draft`, `awaiting_payment` or `paid`. Once an order is `cancelled`, a separate `refunded` true/false flag on it can flip once, if the order was paid.
- `checkout`: draft → awaiting_payment (reserves paper)
- `pay`: awaiting_payment → paid
- `cancel`: draft/awaiting_payment/paid → cancelled (gives the paper back unless it was a draft)
- `start_print`: paid → printing, and back to paid if the print fails
- `ship`: → shipped
- `archive`: shipped → archived (checked by `@allowed_from`)
- `refund`: cancelled and paid → refunded
- The nightly `expire_unpaid` in `jobs.py` cancels orders that sat unpaid for over a day.

**2. Print job** (`printshop/printer.py`)
Can be idle, printing, finished or error, tracked by `printing`, `finished` and `error`, and reported by `describe()`.

**3. Paper stock** (`printshop/stock.py`)
A count of reserved pages: `reserve` adds to it and refuses to go over 1000, `release` takes away from it.

**4. Customer notification settings** (`printshop/models.py`)
Email and SMS are each on or off, and a channel can only be on if the customer gave that contact detail. This one is correct.

## Bugs I fixed

1. **The nightly job never cancelled anything.** It looked for orders with status `"pending"`, which nothing ever sets. Unpaid orders really have status `"awaiting_payment"`, so they never expired and their paper stayed reserved. Fixed in `jobs.py`.
2. **Refunds always failed.** `refund` checked for `"canceled"` (one L), but cancelled orders get `"cancelled"`, so even a paid, cancelled order was refused. Fixed in `orders.py`.
3. **`ship` would ship anything.** It had no check, so a draft, unpaid, paid-but-not-printed or cancelled order could be marked shipped. A shipped order can then be archived, so a cancelled order could end up archived. `ship` now only works on an order that is `printing`.
4. **A printer error jammed the print job for good.** When the printer raised `PrinterError`, the job recorded the error but never cleared `printing`. Every later `start` then raised `PrinterBusy`, so the shop's one printer could never be used again. Fixed in `printer.py`: the job now leaves `printing` when it fails.
5. **An order could get stuck in `printing`.** `start_print` sets the order to `printing` before calling the job. If the job raised an error (for example, because the printer was busy), the order stayed in `printing` with nothing printing it. It could then never be paid, cancelled or reprinted, only shipped. `start_print` now puts the order back to `paid` and passes the error on.

## Things I noticed and left alone

- **Paper reservations are lost between runs.** The reserved-page count only lives in memory and is not saved with the orders. Each command, including `nightly`, starts from 0. Releasing paper there quietly does nothing, because `release` never lets the count go below 0. And the next run's reservations ignore paper already held by saved orders. Fixing this means saving or rebuilding the stock count, which is a design decision, so I left it to you.
- **`release` never lets the count go below 0.** That would hide a double release. Nothing can release twice today, so I didn't change it.
- **Loading saved orders doesn't check the status.** `Order.from_dict` accepts any status string from the saved file. Old data saved with a status like `"pending"` would leave orders stuck. I didn't add a check because I don't know what's in your saved data.
- **Orders expire a day after they were created, not after checkout.** A draft that sat around for a while could be expired soon after checkout. This might be intended, so I left it.
- **Nothing ever moves an order from printing to shipped automatically.** It's left to whoever calls `ship`. That's not a bug, but there's no code for a finished print leading to shipping.

The changes are in `jobs.py`, `orders.py` and `printer.py`, and the new tests are in `tests/test_orders.py`.