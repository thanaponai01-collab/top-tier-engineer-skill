I added `gizmo-pro` at 12.00. My answer is **no, this shouldn't go out today.** The new product isn't the problem. A change already sitting in `app.py` is.

**The change:** `fixture/catalog.py:1` now has `"gizmo-pro": 12.00` in the price list. I placed a test order for one `gizmo-pro` and it went through for 12.00. It also shows up in the public `/catalog` list.

**Test results:** 23 tests ran and 10 failed. All 9 tests in `test_app.py` pass. All 10 failures are in `test_threats.py`.

**The blocker** is `test_export_ignores_requested_customer`. Last time the threat tests were recorded, this one passed. It fails now because `app.py:47` was changed (not by me) from:
```python
invoices.export_csv(user, user.id)
```
to:
```python
invoices.export_csv(user, int(body.get("customer_id", user.id)))
```
That means any logged-in customer can export anyone else's invoices just by sending `customer_id`. In the test, alice gets bob's invoice 101. It looks like it was meant to support staff exports (`test_staff_exports_a_customer`), but nothing checks that the caller is staff. I put the old price list back, ran the test again, and it still failed, so my catalog edit isn't the cause.

**The other 9 failures** were already failing in the earlier record, so they're known open issues:
- Every signup gets 20.00 of free credit, so scripted signups mean unlimited free goods.
- Passwords are stored in plain text.
- The staff password is written in `db.py`.
- Nothing slows down password guessing.
- Five different kinds of bad input crash the server with an error instead of being rejected cleanly.

Whether those are acceptable to ship is your call. They aren't new.

**What I'd do:** either undo the `app.py:47` change, or let `customer_id` take effect only when `user.role == "staff"` and use `user.id` for everyone else. That makes the export test pass again and keeps the staff export working. The catalog addition is safe to ship once that's fixed. I haven't touched `app.py` because I didn't make that change. Do you want me to make the fix?