**Recommendation:** make one edit. In `web/account_form.py`, change the visible label on the existing `display_name` field from `Name` to `Display name`. Then update or add one assertion that the account form shows `Display name`, if there's a form or rendering test nearby.

**Open structural design choices:** none. `fixture/requirements.md` already settles all of them:
- The field name, validation, API, persistence and layout stay the same.
- One file owns the form, so there's no question about where the change goes.
- It says no new component, module, dependency, data or public contract is needed.

So there's nothing to design. Adding a label constant, an i18n layer or a shared component would go beyond the approved scope.

**One thing to check first:** this workspace only contains `fixture/requirements.md`. `web/account_form.py` isn't here, so I couldn't confirm how the label is currently written (a literal string, a `label=` keyword, a template, and so on). That only affects how the one-line change looks, not the plan. If the label `Name` turns out to be shared with other fields or pages, change it only for `display_name`.