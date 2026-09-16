# Latent Audit — fixture/

Swept 12 modules, 3 import edges. One proven layer breach, one module safe to
delete, one suspect that must not be touched.

Layer order taken from the declaration in `ARCHITECTURE.md` (interface >
domain > data), written to a layers file and checked mechanically — not from
taste.

| file / symbol | verdict | proof or unfinished check | action |
|---|---|---|---|
| `app/models/notify.py:2` | breach | proven — imports `app/routes/web.py`, data importing interface | move `BANNER`, or change the declaration |
| `app/services/legacy_export.py` | dead | proven — no import, no string, no config, no CI reference; tests never load it | delete, own commit |
| `app/plugins/csv_out.py` | watch, do not delete | `app/registry.py` resolves it from `ENABLED_PLUGINS` with `importlib` | keep |

`app/models/notify.py` is also statically unreferenced, but it is the breach
above; decide the breach first, then re-check.

`csv_out.render` appears on the unused-definitions list because no import
mentions it. That list is suspects, not findings: the plugin is loaded by name
at runtime. Deleting it would take the CSV output offline.
