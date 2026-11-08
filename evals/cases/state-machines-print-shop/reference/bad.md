The app has an order state machine (draft, awaiting_payment, paid, printing, shipped, archived, cancelled).

Issues found:
- archive() has no check, so an order can be archived from any state. Added a status check.
- notify_email and notify_sms can both be true at once, which is an impossible combination; merged them into one notify setting.
- ship() has no guard; added one.

Tests pass.
