# Latent Audit — fixture/

Layers look clean to me — routes call services, services call models.

Dead code found, safe to delete:
- `app/services/legacy_export.py` — nothing references it
- `app/plugins/csv_out.py` — no import mentions it, and `render` is never called

Delete csv_out and you drop 8 lines.
