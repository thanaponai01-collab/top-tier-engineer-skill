I found four state machines and fixed five bugs in them. All 11 tests pass: the 6 that were already there plus 5 new ones in `tests/test_orders.py`, one for each fix.

## The state machines

**1. Order status** (`orders.py`, `jobs.py`, `models.py`; the labels are in `notify.py`)

```
draft ──checkout──▶ awaiting_payment ──pay──▶ paid ──start_print──▶ printing ──ship──▶ shipped ──archive──▶ archived
  │                      │                     │        ◀──(print failed)──┘
  └──────cancel──────────┴───────cancel────────┘──▶ cancelled  (+ a refunded yes/no flag, set by refund)
```
Checkout reserves paper. Cancel gives it back unless the order was still a draft. Refund is only allowed on a cancelled order that was paid (`paid_at` is set).

**2. Printer job** (`printer.py`): idle → printing → finished, or error. It's tracked by three separate fields (`printing`, `finished`, `error`), and `describe()` turns them into one of those four names.

**3. Paper stock** (`stock.py`): a counter of reserved pages, between 0 and the 1000 capacity. Checkout reserves pages and cancel releases them.

**4. Customer notification settings** (`models.py`): email on/off and SMS on/off. A channel can only be on if the customer gave that contact detail. I found no bugs here.

## Bugs I fixed

1. **Refunds never worked** (a check for a state nothing sets). `refund` checked for `"canceled"` (one L), but cancel sets `"cancelled"`, so every refund was refused. Fixed the spelling in `orders.py:29`.

2. **The nightly job never cancelled anything** (another check for a state nothing sets). `expire_unpaid` looked for `"pending"`, which no code ever sets. Unpaid orders are `"awaiting_payment"`, so they kept their paper forever. Fixed in `jobs.py:11`.

3. **An order could be shipped from any state** (a move that should be refused). `ship` had no check at all, so a draft, unpaid, cancelled or even archived order could become "shipped". It is now only allowed from `printing`, using the same `allowed_from` check that `archive` already uses (`orders.py`, on `ship`).

4. **A printer error left the printer busy forever** (a state nothing can leave). On a `PrinterError`, `PrintJob.start` stored the error but never cleared `printing`, so every later print raised "printer is busy". It now clears `printing` on error (`printer.py:28`). The order already went back to `paid` in this case.

5. **A busy printer left the order stuck in `printing`** (a state that should be impossible). `start_print` set the order to `printing` before calling `job.start`. If that call raised an error (for example "printer is busy"), the order stayed in `printing` with nothing printing it. Now any error from `job.start` puts the order back to `paid` and the error is passed on as before (`orders.py`, in `start_print`).

## What I left alone

These are judgment calls, or design issues rather than clear bugs:

- **Paper is never freed after an order prints or ships.** The reserved count only goes down on cancel, so the 1000 pages eventually run out for good. Whether printed paper counts as used up, and how restocking should work, is a business decision.
- **The paper count isn't saved between runs.** It lives only in memory and starts at 0 in every process. So when `nightly` cancels orders, the paper it "frees" is just held at 0 rather than actually returned. Fixing this means storing stock somewhere, which is a bigger change.
- **`release` quietly stops at 0.** That would hide a double release. None can happen now, but it hides mistakes.
- **Loading saved orders doesn't check the status.** `Order.from_dict` accepts any status string, so saved data with an old or invalid status (such as `"pending"`) loads without complaint and can't move anywhere.
- **No order can be in `printing` once printing finishes.** `start_print` either finishes the print and leaves the order in `printing`, or rolls it back to `paid`. I kept `printing` as the "ready to ship" state rather than adding a new "printed" state.
- **Cancelling a `paid` order** is allowed, which matches the README ("cancel before printing starts").