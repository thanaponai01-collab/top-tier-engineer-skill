Your two complaints in the README, "checkout sometimes takes ages" and "customers were charged but saw an error page", come from the same design mistake. I confirmed it by running the shop's code with the email server switched off.

## How it's supposed to work

Your architecture document (`docs/architecture.md`) describes a sensible setup. Picture a restaurant:

- **The cashier** (checkout) takes the order, checks the item is in stock, charges the card and writes down the order.
- The cashier then **puts a note in a tray**: "send this customer a receipt."
- **A back-office assistant** (the "worker") picks up notes from the tray one by one and sends the emails.

The customer walks away as soon as they've paid. If the email system is slow or broken, only the back office is affected and the customer never notices. Refunds already work this way.

## What the code actually does

Checkout doesn't put a note in the tray. **The cashier sends the receipt email personally, while the customer stands at the counter** (`shop/checkout.py:12`). There's even a comment explaining why: "so the customer has the receipt immediately." It sounds reasonable, but it causes two problems:

**1. Slow checkouts.** When the email server is slow, the cashier waits up to 30 seconds for it. If that fails, they wait 5 seconds and try again, up to 3 times. In the worst case one customer waits about **1.5 minutes** just for a receipt email.

**2. Charged but shown an error.** This is the serious one. The steps happen in this order:

1. Reserve stock ✅
2. **Charge the card** ✅
3. Save the order ✅
4. Send the receipt email ❌ fails

The email is the very last step, so the money has already been taken when it fails. The website still shows the customer an error page. In my test with the email server down, this is exactly what happened:

- Customer saw: `error: mail server unreachable`
- The card was charged and the order was saved
- One mug was taken out of stock

So the customer thinks the purchase failed, but you have their money and you'll ship the item. Many people will then **try again and get charged twice**.

The diagram in your documentation hides this. It shows checkout using the tray, so anyone reading it would think the problem can't happen.

## Smaller problems in the same area

- **The tray loses notes.** The assistant marks a note "done" *before* sending the email (`shop/jobs/queue.py:18`). If sending fails or the program crashes, the note is already marked done and nobody retries it. That customer never gets their refund confirmation.
- **One unknown note stops the back office.** The assistant only knows how to handle refund confirmations. If it picks up a note it doesn't recognise, it crashes, and every email behind it stops being sent.
- **Stock leaks when a card is declined.** Stock is reserved *before* the card is charged, and nothing puts it back if the charge fails. Over time your shop may show items as sold out when they're actually on the shelf.

## What "better" looks like

The overall design doesn't need replacing. The code just needs to do what the documentation already says:

| Today | Better |
|---|---|
| Checkout sends the receipt itself and makes the customer wait | Checkout leaves a note in the tray and responds right away |
| An email failure shows an error to someone who has paid | An email failure only delays the email; the customer still sees "order confirmed" |
| Notes are marked done before the email is sent | Notes are marked done only after the email is sent; failed ones are retried |
| One unknown note stops all emails | Unknown or failing notes are set aside and the rest keep moving |
| A declined card leaves stock reserved | A declined card returns the stock |

The rule behind all of this: **once you've taken someone's money, nothing optional (like an email) should be able to make the purchase look like it failed.** Do the essential steps (stock, payment, order record) while the customer waits, and hand everything else to the back office.

These are small changes, roughly a dozen lines across four files (`checkout.py`, `jobs/worker.py`, `jobs/queue.py` and `inventory.py`). I haven't changed anything yet. Would you like me to make the fixes, or would you rather pass this to a developer?