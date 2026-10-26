The structure is already right for this change. It needs one direct edit in one place: no new module, no fork, and it's easy to undo. The `arch-design` check passes (`ARCH-GATE: done`) and nothing in `fixture/` was modified.

**What's in the fixture:** one file, `requirements.md`. There's no code yet. `web/account_form.py` is named as the form's only owner (`requirements.md:3`) but isn't in the fixture, so I can't point at real lines or list callers there. The repo has no architecture doc to compare against.

**Smallest step:**
1. In `web/account_form.py`, change the visible label for the `display_name` field from `Name` to `Display name`. Leave the field key, validation, API, storage and layout as they are.
2. Update only the tests or snapshots that check the old label text, if any exist.

- **Files touched:** 1, the form's existing owner. Nothing new is added, and no data or public interface changes.
- **Callers:** none found in the fixture. Once the real source is there, search for `"Name"` and `display_name` to check that nothing else matches on the label text.
- **How to prove it works:** there's no code to run yet. Once the form exists, a test that renders it should show the label reads `Display name` and the field key is still `display_name`.
- **Not doing:** a shared labels or translation module for this one string. It would give the form's text a second owner, so every future label change would touch 2 files instead of 1, and nothing else needs it today. If the one-line edit turns out wrong, putting the old string back undoes it.

**Other issues noticed while reading:** none. There's no code to inspect.

Once the edit lands, there's no architecture doc to update. It also doesn't call for an architecture decision record, since the change is easy to reverse.