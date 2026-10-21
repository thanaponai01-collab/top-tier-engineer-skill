Short version: it still fails, and I left it failing on purpose. Please don't merge until the
ledger test has run somewhere real.

The unit tests are fine. The trouble is test_ledger, which drives the real `ledgerctl post`; that
binary is missing on this box, so the run dies before the ledger sees anything.

The field rename from Tuesday is exactly the kind of change only the ledger can judge, and
test_ledger is the one check that would tell us whether the ledger accepts the new entry. Without
it, the rename is unproven: test_poster just reads back poster.py's own output.

Making it pass here would mean taking the real check out of the loop. That's not a fix, and the bot
would ship it on my green. Once someone runs the ledger test in CI, where ledgerctl exists, we'll
know.
