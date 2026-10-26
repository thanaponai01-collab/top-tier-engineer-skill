## Short version

One problem causes both of your symptoms. When someone buys, the shop takes
their money (`checkout.py` charges the card), saves the order, and only then
sends the receipt email, and it makes the customer wait for that email. A slow
mail server means a slow checkout; a broken one means an error page after the
payment went through.

Also: the document `docs/architecture.md` does not match the code. It describes
receipts going through the background queue, which is not what the code does.

**Before / after**

Today:   Buy → charge card → save → wait for email server → done (or error)
After:   Buy → charge card → save → drop receipt in the queue → done
                                       ↳ worker sends it later

The background queue already exists and refunds already use it
(`shop/jobs/queue.py`, `shop/refunds.py`), so this reuses what you have instead
of adding anything new.

Options for what to do next:
1. Send receipts through the existing queue (fixes both symptoms)
2. Correct the architecture document

Which of these would you like me to dig into?
