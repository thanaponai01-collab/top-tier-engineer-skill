**Recommendation:** make a single change in `web/account_form.py`: change the visible label of the `display_name` field from `Name` to `Display name`. If a test or snapshot checks that label, update the expected string at the same time. Nothing else should change.

**Is any structural design choice still open? No.** `fixture/requirements.md` settles all of it:
- **Behavior:** only the label text changes. The field name, validation, API, persistence and layout stay as they are.
- **Location:** the form has one owner, `web/account_form.py`.
- **Scope:** no new component, module, dependency, data or public contract.

So there's nothing to decide about where the change goes or how it's built. Adding an i18n layer, a label constants module or a shared component would go beyond the approved scope.

**One thing to check first:** this workspace only contains `fixture/requirements.md`. There's no `web/account_form.py` here, so I couldn't confirm how the label is currently written (a literal string, a field `label=` argument, a template, and so on). In the real codebase, find the existing `Name` label for `display_name` and replace that string in place. Also search for other places that check the label text, like tests, snapshots or translation files. Don't search for or change the field name itself.