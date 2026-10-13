**Smallest step:** in `web/account_form.py`, change the visible label string on the existing `display_name` field from `"Name"` to `"Display name"`. That's a one-line edit. If a test or snapshot checks the rendered label text, update that assertion in the same change. If there isn't one, add a single assertion that the field renders with the label `Display name`.

**Open structural design choices: none.** The requirements already fix every one:
- **Field name, validation, API, persistence:** unchanged, so there's no data or contract work.
- **Layout:** unchanged, so no markup or styling work.
- **Ownership:** one owner, `web/account_form.py`, so there's no question about where the change goes.
- **New component, module, dependency or abstraction:** explicitly ruled out. Don't add a label constant, an i18n layer or a shared label registry for this.

**One thing to check first:** this workspace only contains `fixture/requirements.md`. `web/account_form.py` isn't here, so I couldn't confirm the current label string or whether a test covers it. Before editing, search the real repo for the literal `"Name"`. That makes sure you change the label on `display_name` and not another field or a shared string. If the label turns out to come from somewhere outside that file, such as a shared translation file, the "one owner" assumption is wrong and you should go back to product before going further.