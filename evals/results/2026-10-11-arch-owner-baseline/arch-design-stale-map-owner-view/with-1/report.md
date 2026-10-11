I ran `arch-design` on the shop. **Overall, the shop is well laid out, but one piece is wired up wrong, and that one piece most likely explains both problems in your README:** checkout that takes ages, and customers who get charged but see an error page.

I chose to **improve** the shop with targeted fixes rather than rebuild any of it. The basic layout is sound.

## How it's supposed to work, and what it actually does

Your design notes (`docs/architecture.md`) describe this order of events:

> Take the stock → charge the card → save the order → **put the receipt email on a "to-do list"** → done. A separate helper (the "worker") sends emails from that list in the background, so the customer never waits.

That's a good design. The code doesn't follow it. At `shop/checkout.py:12`, checkout **sends the receipt email itself, right then, while the customer waits.**

```
What the design says                What the code does
--------------------                ------------------
take stock                          take stock
charge card                         charge card
save order                          save order
add email to to-do list (instant)   SEND EMAIL NOW  <- customer waits here
show "Thank you!"                   show "Thank you!" (only if the email worked)
```

That causes two problems:

1. **Slow checkout.** If the mail server is slow, the email code (`shop/emailer.py:8-16`) waits up to 30 seconds and tries 3 times, pausing 5 seconds between tries. In the worst case **one customer waits about 100 seconds** before seeing anything.
2. **Charged but shown an error.** If all 3 tries fail, checkout gives up and the customer sees an error page. But by then **the card has already been charged, the order is saved and the stock is taken.** The customer thinks the purchase failed when it actually went through.

**I checked this by running it, not just reading it.** I simulated a mail-server outage and placed one test order:

```
customer sees ERROR: mail server down
card charged: [10] | stock left: 4
```

The test customer got an error, was still charged $10, and one item was taken from stock. This matches your README note exactly.

A comment in the code says the email is sent there "so the customer has the receipt immediately." That's a fair goal, but the background helper checks its to-do list every second (`shop/jobs/worker.py:15`), so the receipt would still arrive within seconds.

## What I recommend, in order

### 1. Send receipts through the to-do list, as the design says *(biggest win)*
- **Change:** Checkout adds the receipt to the to-do list instead of sending it. Refunds already work this way (`shop/refunds.py:7`), so the pattern is already in the shop. The background helper also needs to learn to send receipts. Today it only knows refund emails (`shop/jobs/worker.py:6-8`).
- **Result:** Checkout no longer waits on the mail server, so it should stay fast even when email is down, and a mail problem can't show a paying customer an error page anymore.
- **Other option:** keep sending the email during checkout, but don't show an error if it fails. That's simpler, but checkout could still take about 100 seconds. I don't recommend it.
- **How to check it:** run the same mail-outage test again. The customer should see "Thank you" immediately and still be charged once.
- **Risk:** low and easy to undo. It's a two-file change, and nothing about stored data changes.

### 2. Make sure a failed email isn't lost *(do this together with #1)*
Once receipts go through the to-do list, the list has to be reliable. Today it isn't:
- The helper **crosses a job off the list before trying it** (`shop/jobs/queue.py:18`). If the email then fails, the job is marked done and nobody retries it.
- When an email fails, the error isn't caught (`shop/jobs/worker.py:18`), so **the helper itself crashes**. After that, no more emails go out, including refund confirmations, until someone restarts it.

**Better:** cross a job off only after the email is sent, and if one email fails, note it and move on to the next. The other option, a proper job-queue product, is more than a shop this size needs. The current small to-do list is fine once these two lines are fixed.

### 3. Give back stock when a card is declined *(smaller)*
Checkout takes the stock before charging the card (`shop/checkout.py:6-9`). If the card is declined, the stock is never given back, so over time the shop can show items as sold out when they aren't. **Better:** if the charge fails, put the stock back. The other option is to charge first and take stock after, but then you risk charging for something that's out of stock.

### 4. A bigger decision for later: where your data is kept
Orders and stock counts are currently kept only in the program's short-term memory (`shop/db.py:4`, `shop/inventory.py:1`). **If the program restarts, every order record and stock count is lost.** This might be a simplified copy of your real shop. If your real shop works like this, though, it needs a proper database. That decision is hard to undo, so I'd want to talk it through with you, and with an engineer if you have one, before anything changes. The simple starting point would be the kind of storage the to-do list already uses (SQLite, `shop/jobs/queue.py:2`), rather than adding a new service you'd have to run and back up.

## What's fine
Each part of the shop has one clear job: stock, payments, orders, emails and the to-do list. They connect in a sensible direction, and there's no needless complexity. The problems above come from **how the parts are wired**, not from how the shop is laid out.

**The thing to ask your engineer:** "Make checkout put the receipt on the job queue the way refunds do, and make the worker mark a job done only after it succeeds." Those two changes should fix both of the problems in your README.