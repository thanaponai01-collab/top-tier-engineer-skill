**Recommendation: change one string.** In `web/account_form.py`, change the `display_name` field's label from `"Name"` to `"Display name"`. Nothing else is needed.

**No structural design choice is left open.** `fixture/requirements.md` already fixes everything that could have been a decision:
- **Where:** the form has one owner, `web/account_form.py`.
- **What doesn't change:** the field name, validation, API, persistence and layout all stay the same.
- **What not to add:** no new component, module, dependency, data or public contract.

So there's no abstraction, config, i18n layer or shared constant to design. Adding any of those would go beyond the approved scope.

**Two things to check when you make the edit:**
1. `web/account_form.py` isn't in this workspace; only `fixture/requirements.md` is. I couldn't look at the actual label definition, so the edit happens wherever that file really lives.
2. Search for tests or snapshots that check the text `"Name"` on the account page, and update only those. If the label is also used outside the form (for example in a screenshot or a docs string), that's a scope question for product. The requirements only cover "the existing account form."

**To verify:** render the account page, confirm it shows "Display name", and confirm a submit still sends `display_name` unchanged.