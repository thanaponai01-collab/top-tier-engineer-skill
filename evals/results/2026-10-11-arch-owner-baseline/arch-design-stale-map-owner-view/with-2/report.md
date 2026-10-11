I used `arch-design` and read every file in your shop, including the design notes in `docs/architecture.md`. Then I ran the code while pretending the mail server was down, so the problems below were seen happening, not guessed. I didn't change any of your shop's files.

## The short answer

**Verdict: the overall layout is sound, but one important wire is connected to the wrong place.** You don't need a rebuild. You need about three targeted fixes. The first one very likely explains both things in your note: checkout sometimes takes ages, and some customers were charged but saw an error page.

## How checkout is supposed to work

Your design notes describe this order of steps:

```
Customer clicks "Buy"
  1. Set aside the stock
  2. Charge the card
  3. Save the order
  4. Put "send receipt email" on a to-do list   ← the customer doesn't wait for this
  5. Show "Thank you" page

Separately, a background helper works through the to-do list and sends the emails.
```

This is a good design. Sending email is slow and sometimes fails, so it belongs off to the side where the customer never waits for it.

## What the code actually does

The checkout code skips the to-do list and **sends the receipt email itself, while the customer waits** (`shop/checkout.py:12`). The background helper doesn't even know how to send receipts. It only knows refund emails (`shop/jobs/worker.py:6-8`).

So when the mail server is slow or down:
- **The customer waits.** The email code tries 3 times, waits up to 30 seconds each try, and pauses 5 seconds between tries (`shop/emailer.py:8-16`). That's up to **about 100 seconds** of a frozen checkout page. → *"Checkout sometimes takes ages."*
- **Then it gives up and shows an error page.** By then the card has already been charged and the order saved. → *"Charged but saw an error page."*

When I made the mail server fail on purpose, this is exactly what happened: the order was saved with a card charge, and the customer got an error.

There's a note in the code saying the email is sent right there "so the customer has the receipt immediately". That was a reasonable worry, but the background helper checks its to-do list every second. A receipt sent through it still arrives almost immediately.

## The fixes, most valuable first

**1. Send receipts through the to-do list, as your design says.** *(Fixes both complaints.)*
- Teach the background helper to send receipts, then change checkout to add the receipt to the to-do list instead of sending it.
- After this, a mail outage only delays the receipt. The customer gets a fast "Thank you" page, and charged customers never see an error because of email.
- *Other option considered:* keep sending email during checkout but hide the error. That stops the error page but not the up-to-100-second wait, so I don't recommend it.
- *Risk:* low and easy to undo. It's a small code change; no stored data changes shape.

**2. Stop the to-do list from losing emails.** *(Needed once receipts go through it.)*
- The list crosses a job off *before* the email is sent (`shop/jobs/queue.py:18`). If sending fails, the email is lost and never retried. My test confirmed this for refund confirmations, which already lose emails today.
- **Better:** cross it off only after the email is actually sent, so failures get retried later.
- A related small issue: if the to-do list ever contains a task the helper doesn't recognise, the helper crashes and stops sending everything (`shop/jobs/worker.py:18`).
- *Risk:* low and easy to undo.

**3. Give stock back when a checkout fails.**
- Stock is set aside item by item (`shop/checkout.py:6-7`). If a later item is out of stock, the earlier items stay set aside even though nothing was sold. In my test, a failed order permanently made 2 of 5 mugs unavailable.
- I expect the same problem when a card is declined. I couldn't test that, because the payment code is currently a placeholder that never declines.
- **Better:** if the checkout fails at any step, return whatever was set aside.
- *Risk:* low.

## What you don't need

- **No new systems.** Your shop already has a working to-do list for emails. Adding a second, heavier one (the kind big companies use) would mean more to run, secure and pay for, and wouldn't fix anything here.
- **No rewrite.** The pieces are split sensibly. The problems come from a wire going around your own design, not from the design itself.

## One question for whoever runs the shop

Orders and stock levels are currently kept only in the program's memory (`shop/db.py:4`, `shop/inventory.py:1`). If that's what's really running, **every restart erases all orders and stock counts**. This may just be a simplified version, but please ask your developer: *"Where are orders and stock actually stored?"* If the answer is "nowhere permanent", fix that before anything above, because it's the most serious problem. It's also the one decision that's hard to undo, so it deserves a proper choice rather than a quick patch.

## How to check the fixes worked

The failure test I ran is saved at `C:\Users\thana\AppData\Local\Temp\probe\probe.py`. After the fixes, running it again should show:
- the customer gets a success page, not an error;
- the failed email is still waiting to be retried;
- mug stock is back to 5.

If you'd like, I can make fixes 1 to 3 now, each one checked on its own. Or I can write them up as a short brief for your developer.