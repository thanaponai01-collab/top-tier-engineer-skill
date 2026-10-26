The structure is already clean, and this change is a single edit in one file.

The only thing in `fixture/` is `requirements.md`. There's no code, no architecture doc and no tests, and `web/account_form.py`, the file the requirement names as the form's only owner, isn't in the fixture.

**What the requirement says (`requirements.md:3`)**
- The account form has one owner: `web/account_form.py`.
- The change touches 1 file and adds no new modules.
- The field name, validation, API, stored data and layout don't change.

**Smallest step**
1. In `web/account_form.py`, change the label of the existing `display_name` field from `"Name"` to `"Display name"`. Nothing else changes.

- **Reversibility:** easy to undo. No stored data, public API or login code is involved, so I didn't compare alternative designs.
- **Callers:** none in the fixture, since it has no code. The requirement says nothing else owns this form.
- **Reuses:** the existing form, which already holds the label. Nothing new is added.
- **Proof:** I couldn't run any check, because there is no code or test to run. Once `account_form.py` exists, add a check that renders the account form and confirms two things: the label reads `Display name`, and the field is still named `display_name`.
- **Not doing:** a shared label catalog or a new label component. For one string it would add a module and an extra step to every future label change. If a catalog is needed later, moving this string into it is a one-line change.

**Noticed in passing:** nothing, since there was no code to read.

Nothing in the repo was changed, and the skill's helper check passed. The move is ready to implement once `web/account_form.py` is in place.