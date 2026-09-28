# verify-loop over fixture/

**Verdict: do not send the notes. Not every feature is verified.**

`verify.py run`: `2 features | 2 checks pass, 0 fail | 0 unverified | 2 unproven | 1 orphan tests`.

## 1. search.py has no check at all

The code has three features: login, cart and search. VERIFY.md has sections for Login and Cart only.
`search.py` has no section and no test. The tool prints `0 unverified` because it counts only
features that have a section; a feature nobody listed is invisible to it. So "every feature is
verified" is false for search: nothing checks it.

## 2. Both existing checks are unproven

Neither section has a fail-proof line: nobody has broken login or cart and watched a check go red.

## 3. test_legacy_import.py is an orphan and checks nothing

No feature's command names it, and its only test is `self.assertTrue(True)`. It can never fail.

## Blind spots

None listed in VERIFY.md, which the tool flags: a recipe that admits none has not looked.

Next: add a Search section with a check that calls `search()`, prove it fails, then re-run.
