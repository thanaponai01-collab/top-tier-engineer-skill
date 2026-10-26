I ran `arch-design` in design mode over `fixture/`, and it found nothing to restructure. This is a one-line text change in one file, and it can be undone just as easily. I didn't change anything in the repo.

**One thing to know first:** `fixture/` contains only `requirements.md`. The form it names, `web/account_form.py`, isn't in it, so I took the structure from the spec, not from code.

**Verdict:** clean. The label has one owner, so changing the wording means editing one file. No other code uses it, and no API, stored data or contract is involved.

**Smallest step:**
1. In `web/account_form.py`, change the visible label of the existing `display_name` field from `Name` to `Display name`. Leave the field name, validation, API, storage and layout as they are.

- **What else uses it:** nothing; only that form.
- **How to check it:** there's no code yet, so nothing to run. Once the form exists, add a small test that renders it and checks two things: the label reads `Display name`, and the field name is still `display_name`.
- **Option I'm not recommending:** moving labels into a new copy or translation module, or a shared constant. That adds a module and an import in every form, all for one string. If the label edit turns out to be wrong, undoing it is a one-line change with nothing else affected.

Nothing broken or unsafe turned up, though with no code in the fixture there wasn't much to look at. If this is the step you want, the next thing is to make the edit in the real `web/account_form.py` and add the test above.