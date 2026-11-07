The dependencies were in bad shape, and the app wouldn't have run from a clean install. They're fixed now, and all 6 tests pass on a fresh Python 3.12 install of the new `requirements.txt`. While checking, I found a separate bug in the `render` command that I didn't fix; it's at the end.

## What was wrong

- **The Docker image couldn't run the app.** It used Python 3.7, which stopped getting updates in 2023. The code needs at least Python 3.9 (it uses `zoneinfo`), and the pinned `requests` needs 3.8.
- **`click` was missing from `requirements.txt`.** It was listed in `requirements.in`, but the generated file had fallen out of sync. So `pip install -r requirements.txt` produced an install where the command-line tool couldn't even start.
- **Old versions with known security holes:**
  - urllib3 1.24.1, from 2019.
  - Jinja2 2.11.3, which has several published vulnerabilities.
  - PyYAML 5.3.1. Its known hole doesn't affect this app, because the code uses `safe_load`.
- **Jinja2 had been held back on purpose.** A comment said the template uses `@contextfilter`, which Jinja2 3.1 removed. That pin also forced the old MarkupSafe 1.1.1, which won't install cleanly on current Python. In fact the decorator is in `tripbook/render.py`, not the template, and the fix is a one-word rename.
- **`simplejson` was listed but never used.** The code uses Python's built-in `json`.

## What I changed

1. **`Dockerfile`:** `python:3.7-slim` → `python:3.12-slim`.
2. **`tripbook/render.py`:** `contextfilter` → `pass_context`, which is the current Jinja2 name for the same thing. I checked that rendering an itinerary through the filter still gives the right local times.
3. **`requirements.in`:**
   - Removed the Jinja2 pin and its comment; it now requires `Jinja2>=3.1.6`.
   - Raised the minimums for PyYAML and requests.
   - Dropped `simplejson`.
4. **`requirements.txt`:** regenerated for Python 3.12 with every package at its latest version. It now includes `click`, and the other main changes are:
   - urllib3 1.24.1 → 2.8.0
   - Jinja2 → 3.1.6
   - PyYAML → 6.0.3
   - requests → 2.34.2
   - gunicorn 23 → 26.2.0

   I used `uv pip compile`, because `pip-compile` isn't installed on this machine. The header still says `pip-compile requirements.in`, so the README instructions still apply.

## What I left alone

- **`tzdata`:** kept. Slim containers and Windows need it for time zone names like "Asia/Bangkok".
- **gunicorn and urllib3:** both jumped major versions. The web app is a tiny plain WSGI function and `requests` supports urllib3 2.x, so the risk is low. But the tests don't cover either of them; I only checked that both import.
- **Docker:** I didn't build the image, so the Dockerfile change hasn't been run.

## A separate bug I found

`python -m tripbook render trips/bangkok.yaml` crashes with `'dict object' has no attribute 'depart_dt'`. The template asks for `leg.depart_dt`, but neither the code nor the trip file provides it. This has nothing to do with the dependencies; before, it was just hidden because the command crashed earlier on the missing `click`. I left it alone because it's a code decision. Adding `depart_dt` to each leg (via `parse_time`) in `cli.py` would fix it.

## What you need to decide

1. **Python version:** I picked 3.12 as a safe, widely supported choice. Change it if you deploy on something else, and regenerate `requirements.txt` for the same version.
2. **`simplejson`:** I removed it because nothing imports it. Put it back if something outside this repo relies on it.
3. **The `render` bug:** whether you want me to fix it.