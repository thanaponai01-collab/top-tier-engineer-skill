I read all the shop's code (about 130 lines). There's one main problem, and it probably explains both symptoms in your README: checkout taking ages, and customers being charged but seeing an error page.

## The short version

Your design document says the shop works one way, but the code works another way.

**What the document says:** when someone checks out, the shop takes the payment, saves the order, and writes "send this customer a receipt" on a to-do list. A separate background helper works through that list later. The customer never waits for the email.

**What the code does:** checkout skips the to-do list and sends the receipt email itself, while the customer waits on the checkout page.

Think of a café. The cashier is supposed to take your money, hand the order slip to the kitchen and serve the next customer. Instead, this cashier takes your money, then walks to the post office to mail your receipt before telling you the payment went through.

## Why this causes both of your symptoms

**1. "Checkout sometimes takes ages."**
If the email server is slow or down, the shop gives it 30 seconds to respond. If that fails, it waits 5 seconds and tries again, up to 3 times. In the worst case, the customer looks at a loading page for **about 100 seconds**, and all of that is spent on the receipt email, not the purchase.

**2. "Charged but saw an error page."**
The steps happen in this order:

```
1. Set aside the stock        ✅
2. Charge the card            ✅  ← money is taken
3. Save the order             ✅
4. Send the receipt email     ❌  ← email server fails all 3 tries
5. Show "Thank you" page      ⛔  never reached → customer sees an error
```

By step 4 the money is taken and the order is saved. When the email fails, the shop gives up on everything that comes after it, so the customer sees an error. They think the purchase failed, but they've paid. They might try again and pay twice.

## What better looks like

Make the code do what your design document already describes:

```
Customer's checkout (fast)            Background helper (no rush)
──────────────────────────            ───────────────────────────
1. Set aside stock                    
2. Charge card                        
3. Save order                         
4. Add "send receipt" to to-do list ──▶ Picks it up and sends the email.
5. Show "Thank you" ✅                  If the email server is down,
                                        it can try again later. The
                                        customer is never affected.
```

Checkout then never depends on the email server. A slow email server just means the receipt arrives a few minutes late, which nobody minds.

Your refunds already work this way. Only checkout was done differently.

## Two smaller issues the fix should also handle

1. **The background helper doesn't know how to send receipts.** It only knows how to send refund confirmations. So it isn't enough to move the receipt onto the to-do list; the helper also has to learn that task. Otherwise receipts would pile up unsent, or the helper would crash.
2. **The helper ticks a task off before doing it.** If an email fails, the task is already marked done and is silently forgotten. It should only tick a task off once the email has actually gone out, so failed emails get retried. Right now this affects refund emails too.

## What I'd suggest

The fix is small: a handful of lines in three files (checkout, the background helper and the to-do list). An engineer could do it in an afternoon, and I can make the change if you'd like. Your design document doesn't need to change, because it already describes the right design.

For the customers who were charged but saw an error: their orders were saved, so you should be able to find them, confirm their purchase, and check whether anyone paid twice.