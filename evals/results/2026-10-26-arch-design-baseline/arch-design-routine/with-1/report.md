This is a settled copy change, so the skill's "settled small changes stay direct" rule applies. That means no candidate cards, no competing designs and no before/after diagrams.

**Verdict:** No structural change is needed. It's a one-line label edit in the one module that owns the form.

**Structure**
- **Owner:** `web/account_form.py`, the account form's only owner according to `fixture/requirements.md`. The label belongs there.
- **Unchanged:** the `display_name` field name, validation, API, persistence and layout.
- **Not adding:** a label constants file, an i18n layer or a shared component. One string has one caller, so a separate place for it would be a structure nobody needs. If localization is ever requested, that's when to add one.

**Smallest step**
1. In `web/account_form.py`, change the `display_name` field's label from `Name` to `Display name`. Change nothing else.
2. If a test or snapshot checks the label text, update that expectation in the same change. Tests on the field name, validation or API should pass without edits. If one of them fails, the change went beyond the agreed scope.

**Proof:** render the account page or form and confirm the label reads `Display name`. Submit the form and confirm the request still sends `display_name` and the value saves as before. Running the existing form tests with only the label assertion changed covers the rest.

**Door:** two-way. It's visible copy only, with no stored shape or public contract, so it can be reverted in one line.

**Caveat (suspected, not traced):** `fixture/` contains only `requirements.md`. `web/account_form.py` isn't there, and there's no architecture map or ADRs. So I can't confirm the claims that the form has one owner and that the label lives in one place. Before editing, search for the literal `"Name"` near `display_name`, for example in templates or a duplicate form definition, to check that this really is a single edit.

Nothing has been changed. If you want to build it, the next step is a one-line edit; send me the real `web/account_form.py` and I can make it.