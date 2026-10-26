I read the whole shop (it's small, about 130 lines). The main problem is one decision in the checkout step, and it explains both things in your note: checkout being slow, and customers being charged but seeing an error page.

## How checkout works today

When a customer clicks "Buy", the website does these steps one after another while the customer watches a loading spinner:

```
Customer clicks "Buy"
   │
   ▼
1. Set aside the items in stock
2. Charge the card                 ← money is taken here
3. Save the order
4. Send the receipt email          ← customer is STILL waiting
   │
   ▼
Customer sees "Order confirmed"
```

Step 4 is the problem. Your shop has a separate "back office" system: a to-do list (a queue) and a helper (a worker) that works through it, built so emails can go out without making anyone wait. Your design document says checkout uses it: *"puts the receipt email on the job queue. The customer never waits for email."*

**The code doesn't do that.** Checkout sends the receipt email itself, right there in step 4 (`shop/checkout.py:12`). A comment beside it says this is so the customer "has the receipt immediately". Someone probably changed it on purpose and the document was never updated.

## Why this causes both of your problems

Think of a cashier who, after taking a customer's money, phones the post office to mail the receipt and won't hand over the bag until the call goes through.

**"Checkout sometimes takes ages."** If the email server is slow or down, the code waits up to 30 seconds for it, pauses 5 seconds, and tries again, three times in total (`shop/emailer.py:8-16`). That's **over a minute and a half** of the customer staring at a spinner.

**"Charged but saw an error page."** If all three tries fail, the code gives up with an error. By then the card has **already been charged** and the order **already saved**, but the error stops everything, so the customer sees an error page instead of their confirmation. From their side it looks like the purchase failed. In reality it went through, and only the receipt failed.

## What better looks like

Send the email the same way refunds already do. Refunds hand their email to the back office and move on (`shop/refunds.py:7`).

```
Customer clicks "Buy"
   │
   ▼
1. Set aside the items in stock
2. Charge the card
3. Save the order
4. Put "send receipt" on the to-do list   ← takes a split second
   │
   ▼
Customer sees "Order confirmed" right away

                 Meanwhile, in the back office:
                 Worker picks up "send receipt" → sends email
                 (if the email server is slow, only the worker waits)
```

The customer gets their confirmation within a second or so. The receipt still arrives seconds later, and a slow email server can no longer turn a successful order into an error page.

## Three smaller problems I found along the way

1. **The back-office helper only knows how to send refund emails.** It has no instructions for "send receipt" (`shop/jobs/worker.py:6-8`). The fix above needs that added, or the helper will stop when it reaches its first receipt.
2. **The helper ticks a job off before doing it** (`shop/jobs/queue.py:18`). If an email fails, the job is already marked done and won't be tried again, so that customer never gets the email. It should tick the job off only after the email actually goes out.
3. **If a card is declined, the items stay set aside.** Stock is reserved before the charge, and nothing puts it back when the charge fails (`shop/checkout.py:6-9`). Over time this can make items look sold out when they aren't.

## In plain terms

| | Today | Better |
|---|---|---|
| Slow email server | Customer waits 90+ seconds | Customer doesn't notice |
| Email server down | Charged, but sees an error | Sees confirmation; email is retried |
| Failed email jobs | Silently lost | Retried until sent |
| Declined cards | Stock gets stuck | Stock is released |
| Design document | Says one thing, code does another | Matches again |

The main fix is small: change one line in checkout and add one entry to the helper's instructions. The other three are each a few lines. I haven't changed anything yet. If you want, I can make these fixes and give you a short summary of what changed that you could pass to whoever maintains the shop.