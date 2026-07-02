# Patch 05 — Search wildcards + DEBUG + secret (resolves F7)

## LIKE metacharacter escaping
`app/controller/shows.py` — escape `%` and `_` in user input before interpolation:
```python
def _like(term):
    term = term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{term}%'

# usage:
.filter(Event.name.like(_like(name), escape='\\'))
```
Apply to `getShowsByName`, `getShowsByDescription`, `getShowsByTags`.

## DEBUG from environment, default False
`app/utils/config.py`:
```python
DEBUG = os.environ.get('FLASK_DEBUG', '') == '1'
SECRET_KEY = os.environ['APP_SECRET_KEY']   # no default; fail loudly if unset
```
`main.py` — delete the line `Config.DEBUG = True`.

**Why:** Flask's `DEBUG=True` exposes the Werkzeug interactive debugger — arbitrary code execution
to anyone who can trigger an exception on a reachable instance. The committed `SECRET_KEY` is now
compromised (it was in git history); rotating it to an env var is mandatory alongside patch 02.

**Pre-verify:** start the app with no `FLASK_DEBUG` — confirm `app.debug is False`; start with no
`APP_SECRET_KEY` — confirm it refuses to boot rather than falling back to a known key.
