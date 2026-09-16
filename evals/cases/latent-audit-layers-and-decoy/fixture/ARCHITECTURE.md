# Architecture

Three layers. A module may import its own layer or a lower one, never a higher one.

1. `app/routes/`   — interface. HTTP in, HTTP out.
2. `app/services/` — domain. Business rules.
3. `app/models/`   — data. Storage and records only.

`app/plugins/` are output formats. They are never imported; `app/registry.py`
resolves them by name at runtime from `ENABLED_PLUGINS`.
