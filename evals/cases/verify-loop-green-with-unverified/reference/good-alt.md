I would hold the release notes.

Green here means two checks passed, one for login and one for cart. That is all it means.

- Search: `search.py` works when I call it, but VERIFY.md never mentions it and no test touches it.
  The run summary says 0 unverified only because the tool cannot count a feature that has no
  section. Nothing verifies this feature, so the sentence about every feature would be untrue.
- The login and cart checks have never been made to fail (the tool says 2 unproven), so even the
  green ones are unearned.
- test_legacy_import.py is attached to no feature, an orphan, and its single assertion is
  assertTrue(True). It checks nothing and inflates the count.

Send the notes only after a search check exists and each check has been seen red.
