Order lifecycle: draft -> awaiting_payment -> paid -> printing -> shipped -> archived, with cancelled reachable from draft, awaiting_payment and paid. Print job: idle, printing, finished, error.

Found four bugs and fixed them:
1. A typo: refund() compares against "canceled" (one l) while cancel() sets "cancelled", so paid orders that were cancelled can never be refunded.
2. expire_unpaid() matches "pending", which no code writes any more; it should be awaiting_payment, otherwise unpaid orders never expire and the paper stays reserved.
3. After a jam (PrinterError) PrintJob leaves printing = True, so the printer stays busy forever. Reset it in the error path.
4. ship() does no check, so a cancelled order could be shipped. Added a guard (only from printing).

Left alone: the two notify flags are independent, any combination is fine. archive() is guarded by the allowed_from decorator.
