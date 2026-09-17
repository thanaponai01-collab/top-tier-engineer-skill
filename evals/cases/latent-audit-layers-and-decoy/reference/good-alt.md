# Audit — fixture/

The layer order is not my opinion: `ARCHITECTURE.md` declares it, routes above
services above models, and that declaration is what the check below is against.

**One breach.** `app/models/notify.py` imports `app/routes/web.py`. That is the
data layer reaching up into the interface layer — the wrong direction, and the
one import here that the declared order forbids. It also makes the models package
unimportable without dragging the web layer in behind it.

**One thing is genuinely dead.** `app/services/legacy_export.py`: no module
imports it, and no string anywhere in the tree names it either, which is the
check that matters in a codebase that resolves modules by name. Safe to delete.

**One thing only looks dead — do not delete `app/plugins/csv_out.py`.** It has no
importer in source, so every naive sweep flags it. `ENABLED_PLUGINS` in the
settings names it as a string and the registry imports that name at run time, so
removing the file breaks the loader at startup. Its `render()` is the entry point
the registry calls through; it is not unused either. Leave both alone.
