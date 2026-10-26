**Recommendation:** make one edit in `web/account_form.py`: change the visible label on the `display_name` field from `Name` to `Display name`. If a test checks the rendered form, update or add one assertion on the label text. Don't change anything else.

**Open design choices:** none. `fixture/requirements.md` already decides everything a design discussion would cover:
- **Where the change goes:** the form has one owner, `web/account_form.py`.
- **What stays the same:** the field name, validation, API, how the value is saved, and the layout.
- **What's not needed:** no new component, module, dependency, data, or public contract.

So there's no reason to add a label constant, an i18n layer, or a shared component for this. It's a one-line copy change.

**One problem:** this workspace contains only `fixture/requirements.md`. There is no `web/account_form.py` here, so I can't point to the exact line or confirm how the label is written (for example a `label=` argument or a template string). Once the real file is available, the change is a single string replacement there.