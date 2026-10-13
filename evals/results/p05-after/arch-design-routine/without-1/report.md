**Smallest step:** change one string in `web/account_form.py`, the visible label for `display_name`, from `Name` to `Display name`. Nothing else changes.

**Open structural choices:** none. `fixture/requirements.md` already settles everything a design decision could touch:
- The field name, validation, API, persistence and layout all stay the same.
- The form has one owner, `web/account_form.py`.
- No new component, module, dependency, data or public contract is needed.

So there's no abstraction or new file to decide on, and no reason to plan further. Any refactor beyond the label would go past the approved scope.

**How to check it's done:** the account form shows `Display name` for the `display_name` field. The field's name, its validation and the request it submits are unchanged. If a test or snapshot checks for the old `Name` label, update it to the new text in the same change. If none exists, one small assertion on the label is enough.

**What's missing here:** this workspace only contains `fixture/requirements.md`. There is no `web/account_form.py`, so I couldn't find the label line or check for tests that mention `Name`. Before editing in the real repo, search for the `Name` label to confirm the form is the only place it appears. Other text like page headings may also say "Name" and should stay as is.