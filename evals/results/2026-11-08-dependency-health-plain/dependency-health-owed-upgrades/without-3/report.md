I made the dependency changes and the tests pass (6/6) in a fresh Python 3.13 environment installed from the new lock file. One thing in the app was already broken before I started and still is (details at the end).

## What I changed

1. **Jinja2 2.11.3 → 3.1.6.** It was pinned to an old version with several known security holes. The pin was only there because `tripbook/render.py` used `@contextfilter`, which newer Jinja2 removed. I switched it to the new name, `@pass_context`, a one-word change, and dropped the pin. MarkupSafe went from 1.1.1 to 3.0.4 along with it.
2. **PyYAML 5.3.1 → 6.0.3.** The old version has a known security flaw. Your code uses `safe_load`, so it wasn't exposed, but 5.3.1 also won't install on current Python versions.
3. **urllib3 1.24.1 → 2.8.0.** This is the library `requests` uses underneath. 1.24.1 is from 2019 and has several known security holes.
4. **Added `click` to the lock file.** The CLI needs it and it was listed in `requirements.in`, but it was missing from `requirements.txt`. So `pip install -r requirements.txt` gave you an install where `python -m tripbook` crashed.
5. **Removed `simplejson`.** Nothing uses it; `rates.py` uses the built-in `json`.
6. **Regenerated `requirements.txt`** with every package at its current version (requests 2.34.2, gunicorn 26.2.0, certifi, idna, tzdata, etc.). I used `uv pip compile`, which works like `pip-compile`, so the README instructions still apply.
7. **Docker image: `python:3.7-slim` → `python:3.13-slim`.** The 3.7 image could never have worked:
   - `times.py` uses `zoneinfo`, which only exists from Python 3.9.
   - The pinned `requests` and `packaging` need 3.8 or newer.
   - Python 3.7 stopped getting security fixes in 2023.

## How I checked it
- Unit tests: 6/6 pass.
- `python -m tripbook rates EUR` fetched real exchange rates.
- The web module loads.
- **Not checked:** I couldn't build the Docker image or run gunicorn here, because gunicorn doesn't run on Windows. Please run `docker build` once to confirm.

## What I left alone
- **`tzdata`:** kept, because `zoneinfo` needs it on Windows and on slim images.
- **`render` command, already broken:** `python -m tripbook render trips/bangkok.yaml` fails with `'dict object' has no attribute 'depart_dt'`. The template asks for `leg.depart_dt`, but the trip files only provide `depart` as text, and nothing turns that text into a date. This has nothing to do with the dependencies; the old versions would fail the same way. I didn't fix it because how the app should work isn't a call I should make while doing a dependency cleanup.

## What you need to decide
1. **Python version:** I picked 3.13 and built the lock file for it. If production needs a different version, change the `FROM` line and regenerate the lock file for that version.
2. **The `render` bug:** do you want it fixed? The simple fix is to turn `depart` into a date when the trip file is loaded. The tests only cover `itinerary.py`, so nothing caught this. A small test for `render` would be worth adding.
3. **gunicorn 23 → 26:** a big version jump. The app is a plain WSGI function, so I expect no problems, but I couldn't run it to confirm.