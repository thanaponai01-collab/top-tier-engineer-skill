I found four state machines and fixed five bugs. All 11 tests pass: the 5 that were already there and 6 new ones I added for these bugs.

## The state machines

**1. Order status** (`printshop/orders.py`, plus `jobs.py` and `guards.py`)
`draft → awaiting_payment → paid → printing → shipped → archived`, and `draft / awaiting_payment / paid → cancelled`. There's also a separate `refunded` flag that should only be set on a paid order that was then cancelled.
- `checkout` (draft → awaiting_payment, reserves paper), `pay`, `cancel` (gives paper back unless the order was still a draft), `start_print`, `ship`, `archive` (guarded with `@allowed_from("shipped")`).
- The nightly job `expire_unpaid` is meant to cancel orders left unpaid for a day.

**2. Print job** (`printshop/printer.py`): idle → printing → finished, or → error. It's tracked with the `printing`, `finished` and `error` fields.

**3. Paper stock** (`printshop/stock.py`): a count of reserved pages that checkout adds to and cancel takes away from.

**4. Customer notification settings** (`models.py`, `notify.py`): email and SMS on or off, and each can only be on if the customer has that contact detail.

## Bugs I fixed

1. **Refunds could never happen** (`orders.py:29`). `refund` checked for `"canceled"` (one L), but the code only ever sets `"cancelled"`. Every refund was refused. Fixed the spelling.
2. **The nightly expiry did nothing** (`jobs.py:11`). It looked for `"pending"`, which nothing ever sets. Unpaid orders are `"awaiting_payment"`, so they never expired and their paper was never freed. It now looks for `"awaiting_payment"`.
3. **`ship` accepted any order** (`orders.py:51`). It had no check, so a draft, unpaid, cancelled or archived order could be marked shipped. It now only works on an order that is `printing`.
4. **A printer error left the printer stuck** (`printer.py:28`). On a printer error, `PrintJob.start` recorded the error but left `printing = True`. After that, every later print raised "printer is busy", so the one printer was out of action for good. It now clears `printing` when it records the error.
5. **An order could get stuck in "printing"** (`orders.py:40`). `start_print` sets the order to `printing` before calling the printer. If the printer raised an error instead of returning False (for example "printer is busy"), the order stayed `printing` with nothing actually printing. Shipping was the only way out of that state. It now goes back to `paid` and the error is passed on.

## Things I left alone

- **Saved statuses aren't checked on load** (`Order.from_dict`). Any string in `orders.json` is accepted as a status. I'd only add a check once you decide what should happen to bad data.
- **Paper stock isn't saved.** The reserved count lives in memory and starts at 0 each time the program runs. When the nightly job cancels an order, `release` hides the problem by never going below 0, so it doesn't actually free anything. Fixing this needs a decision about where the stock count is stored, so I didn't change it.
- **Paper for printed orders is never released.** That looks deliberate, since the paper has been used, so I treated it as correct.
- **Expiry counts from when the order was created**, not from checkout, because no checkout time is stored. It's close enough to "after a day" that I kept it.
- **Draft orders can be cancelled.** That matches the README, which says a customer can cancel before printing starts.
- **The notification settings are fine.**