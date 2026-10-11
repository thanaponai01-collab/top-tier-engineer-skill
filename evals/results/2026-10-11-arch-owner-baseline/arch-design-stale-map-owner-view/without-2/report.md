I read every file in the shop. The design is mostly sound. The problem is that the code doesn't follow its own plan, and that one gap likely explains both of the things in your note: slow checkouts, and customers who were charged but saw an error page.

## How checkout is supposed to work

The shop's design document describes a checkout counter with a back office behind it:

```
Customer ──► Checkout counter ──► 1. Set aside the items
                                  2. Charge the card
                                  3. Write down the order
                                  4. Drop "send receipt" note in the outbox ──► Back office sends the email later
                                  5. Tell customer "Done!"
```

The customer never waits for the email. The checkout counter drops a note in the outbox, and a separate back-office worker sends the email later. This is a good design.

## How it actually works

The checkout code skips the outbox. The cashier sends the receipt email personally, while the customer waits:

```
Customer ──► Checkout counter ──► 1. Set aside the items
                                  2. Charge the card        ✅ money taken
                                  3. Write down the order   ✅ order recorded
                                  4. Personally send email  ⏳ ...waiting on the mail server...
                                  5. Tell customer "Done!"
```

Step 4 is where both of your problems come from.

**Slow checkout.** If the mail server is slow, the email code waits up to 30 seconds. Then it pauses and tries again, up to three times. In the worst case, the customer stares at a loading page for about **100 seconds** while their card has already been charged.

**"Charged but saw an error."** If all three email attempts fail, the error travels back to the customer as an error page. By then steps 2 and 3 have already happened. The money is taken and the order exists, but the customer is told something went wrong. They may try again and get charged twice.

In short, a problem with *email*, the least important step, can ruin a checkout that had already succeeded.

## What better looks like

**1. Make checkout match the design.** Checkout should drop a "send receipt" note in the outbox instead of emailing directly. Checkout then always takes a fraction of a second, and an email outage can never show a paying customer an error. Refunds already work this way. Checkout is the one part that breaks the rule. This is the main fix.

**2. Make the back office reliable.** The back-office worker has two weaknesses, and once receipts go through it they start to matter:
- **It ticks a job off before doing it.** It marks a note "done" first and then tries to send the email. If sending fails, the note is already ticked off, so that customer's email is silently lost. It should tick it off only after the email is sent, and retry later if sending fails.
- **One failure stops it completely.** A single failed email crashes the worker, and no further emails go out until someone restarts it. It should record the failure and move on to the next note.

**3. Give back reserved stock if payment fails.** Checkout sets aside the items before charging the card. If the card is declined, nothing puts those items back, so your stock count shrinks a little with every declined card. It should release them when payment fails.

## Priority

| # | Change | Fixes | Effort |
|---|--------|-------|--------|
| 1 | Checkout uses the outbox for receipts | Slow checkouts and charged-but-error pages | Small: a few lines |
| 2 | Back office ticks jobs off only after success, and keeps going after a failure | Lost receipt and refund emails | Small |
| 3 | Put stock back when a card is declined | Stock counts slowly drifting too low | Small |

All three are small changes, and item 1 should go first. Fixes 1 and 2 belong together: once receipts go through the outbox, the back office has to be dependable.

I haven't changed any code. I can make these fixes for you, or write a short summary to hand to whoever maintains the shop.

For whoever reads the code: the direct email call is at `shop/checkout.py:12`, the retry loop is at `shop/emailer.py:8-16`, and the worker marks jobs done before running them at `shop/jobs/queue.py:18`. The worker also has no receipt handler yet (`shop/jobs/worker.py:6`).