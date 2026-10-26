I read the whole shop (it's small, about 130 lines). I also read the architecture document that describes how it's supposed to work. The main problem is that **the document and the actual shop disagree.** That one gap explains both complaints in your README: checkout sometimes takes ages, and some customers were charged but saw an error page.

## How it's supposed to work (according to your docs)

Think of the shop as a restaurant. When a customer pays, the cashier should take the money, hand over the order number, and pin a note on the board for the back office: "email this person their receipt." The customer leaves. Someone in the back office (the "worker") sends the emails later.

```
Customer pays ──► Cashier: reserve stock → charge card → record order → pin note on board ──► "Thanks!" ✅
                                                                              │
                                                       Back office (later) ◄──┘  sends the receipt email
```

Your docs say exactly this: *"The customer never waits for email."*

## How it actually works

The cashier doesn't pin a note. They phone the mail server themselves, while the customer stands at the counter waiting. Someone left a comment in the code saying this was done on purpose, "so the customer has the receipt immediately." It was a well-meant shortcut, but it causes your two problems.

```
Customer pays ──► reserve stock → charge card 💳 → record order → cashier phones mail server ☎️ ... waiting ...
                                                                          │
                                         mail server slow? ──► customer waits up to ~1.5 minutes
                                         mail server down? ──► customer sees ERROR page ❌ (but card already charged)
```

**Problem 1: "Checkout sometimes takes ages."** When the mail server is slow, the cashier keeps trying. They try up to 3 times, wait up to 30 seconds each time, and pause 5 seconds between tries. A customer can be stuck on the checkout page for about a minute and a half just waiting for an email.

**Problem 2: "Charged but saw an error page."** The card is charged *before* the email is attempted. If all 3 email attempts fail, the shop gives up and shows the customer an error. By then the money has been taken and the order recorded. The order succeeded; only the receipt email failed. The customer can't know that, so they think the purchase failed. They might try again and get charged twice.

## Three smaller problems with the same root cause

These come from the same weakness: steps happen in sequence, and nothing cleans up when a step fails.

1. **Stock can go missing.** Items are set aside before the card is charged. If the card is declined, they are never put back. Over time the shop can believe it's out of stock when it isn't.
2. **The back office throws notes away before reading them.** The worker crosses a job off the board *before* doing it. If the email then fails, for example a refund confirmation, the job is already marked done and nobody ever retries it. The customer silently gets no email.
3. **The back office doesn't know how to send receipts.** Its instructions only cover refund confirmations. So you can't fix this just by moving receipts to the queue; the worker also has to be taught to send them.

## What better would look like

```
Customer pays ──► reserve stock → charge card → record order → pin "send receipt" note ──► "Thanks!" ✅ (fast, always)
                     │               │
                     └─ card fails? put the stock back, show a clear "payment declined" message

Back office: take note → send email → only THEN cross it off
                                   └─ failed? leave it on the board and try again in a few minutes
```

In plain terms:

- **Checkout does only what the customer must wait for:** stock, payment and order. The receipt goes on the queue, as your docs already promise. Checkout becomes quick and predictable, and a mail problem can never show a paying customer an error page.
- **Undo on failure:** if the card is declined, the reserved stock is put back.
- **The back office only crosses a job off once it's actually done,** and retries the ones that failed. Emails arrive a little late instead of never.
- **Receipts are added to the back office's instructions.**

None of this is a rewrite. Each change touches only a few lines. The first one (moving the receipt email off the checkout path) fixes both of your complaints by itself, so I'd do it first.

One more thing to raise with whoever builds the shop: in this code, orders and stock levels are held only in the program's memory. If that's true of the real shop, restarting the server would erase them. This copy may be a simplified version, so it's worth a quick question to your developer.

Would you like me to make these changes, or write them up as a short brief for your developer?