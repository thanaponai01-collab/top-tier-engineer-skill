I ran `arch-design` in design mode. **This change needs no new structure: it's a one-line label edit in the form's existing owner.**

**What's in `fixture/`:** only `requirements.md`. The file it names as the form's owner, `web/account_form.py`, isn't in the fixture. So I couldn't read where the label is set; everything below comes from the requirements alone.

**The settled change** (from `fixture/requirements.md`):
- **Changes:** on the account form, the visible label for `display_name` goes from `Name` to `Display name`.
- **Stays the same:** the field name, validation, API, how it's saved, and the layout.

**Structure:** keep it as it is. One file owns the form, so there's no new component, module, helper, dependency or data change, and no setting to make the label configurable. A seam or a shared "labels" module would only add work for one string.

**Smallest step:**
1. In `web/account_form.py`, change the label text for `display_name` from `"Name"` to `"Display name"`. Leave the field key `display_name` alone.
2. **Proof:** render the account form and check that the label reads `Display name`, and that saving the form still sends `display_name` with the same validation. If a test checks the old label, update that one expected string.

**How hard to undo:** easy. It's visible text only, and reverting is the same edit backwards. No stored data or public contract changes, so no decision record is needed.

**Before editing, search the codebase for the literal `"Name"`.** Other code may depend on the visible text, such as end-to-end tests, screenshots, translation files, or analytics. If any does, update it in the same change. I couldn't run this search because the source isn't in the fixture.