# accounts

Sign-up and plans. `app/` is the code, `migrate.py` the schema migrations (`up`, `down TARGET`,
`status`), `data/app.db` the database (set `APP_DB` to use another file).

    python -m unittest discover tests

`./deploy.sh` pulls, runs `python migrate.py up`, and restarts the services.
