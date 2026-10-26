# crm

Contacts and their notes. `app/` is the web app, `api/v1.py` the old JSON API, `exports/` the weekly
CSV, `migrate.py` the schema migrations (`up`, `down TARGET`, `status`). Everything reads
`data/crm.db` (set `CRM_DB` to use another file).

    python -m unittest discover tests

`./deploy.sh` pulls, runs `python migrate.py up`, then restarts the services; until they restart
(about a minute) the old code serves requests on the new schema.
