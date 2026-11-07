The dependencies were in bad shape. They're fixed now, and all 6 tests pass on a fresh install of the new lock file.

## What was wrong
- **The dependencies couldn't be installed on a current Python.** PyYAML 5.3.1 fails to build on Python 3.13.
- **The Docker image couldn't build either.** It used Python 3.7, which stopped getting updates in 2023. It is also too old for the pinned `requests` 2.32.4, and the code uses `zoneinfo`, which only exists from Python 3.9 on.
- **`click` was missing from `requirements.txt`.** The command-line tool depends on it, so a clean install from the lock file would crash on `python -m tripbook`. The lock file had drifted from `requirements.in`.
- **Old pins with known security holes:** urllib3 1.24.1 (from 2019), Jinja2 2.11.3 with MarkupSafe 1.1.1, and certifi 2024.7.4 (an old list of trusted certificates).
- **The note explaining the Jinja2 pin was wrong.** It said the template used `@contextfilter`. The template doesn't; one line in `tripbook/render.py` does, and that's an easy rename.

## What I changed
- **`requirements.in`:** Jinja2 is no longer pinned to 2.11.3 (now `>=3.1`), PyYAML is now `>=6.0`, and the wrong note is gone. I also removed `simplejson` because nothing imports it (`rates.py` uses the standard `json` module). I added a short note saying why `tzdata` is needed.
- **`requirements.txt`:** regenerated with `pip-compile --upgrade`, so every package is on its current version. Jinja2 is now 3.1.6, urllib3 2.8.0, requests 2.34.2, PyYAML 6.0.3, gunicorn 26.2.0, and `click` 8.5.1 is now included.
- **`tripbook/render.py`:** `contextfilter` is now `pass_context`, its replacement in Jinja2 3.
- **`Dockerfile`:** the base image moves from `python:3.7-slim` to `python:3.13-slim`.

## How I checked it
- **Tests:** passed, and `pip check` found no conflicts.
- **`rates EUR`:** prints live rates.
- **Web app:** returns its 200 response when called directly.
- **Rendering with Jinja2 3:** works when the leg times are given as datetimes.
- **Not tested:** the Docker build (Docker isn't installed here) and gunicorn itself (it doesn't run on Windows).

## What I left alone
- **`tzdata`:** kept, because the slim Docker image and Windows don't include a timezone database, and `zoneinfo` needs one.
- **gunicorn:** it jumped from 23 to 26. The app is a plain WSGI function and the start command uses only basic options, so I expect no trouble. It's still the change most worth watching on the first deploy.

## What you need to decide
1. **`python -m tripbook render` was already broken, and still is.** The template asks for `leg.depart_dt`, but nothing in the code creates it, so it fails with "has no attribute 'depart_dt'". That's a bug in the app, not in the dependencies, so I didn't touch it. The likely fix is for `render_cmd` to turn each leg's `depart` text into a datetime before rendering. I tested that and it gives correct times, e.g. "Sun 01 Mar 16:30" for the London departure shown in Bangkok time. Should I make that change?
2. **Removing `simplejson`:** if something outside this repo relied on it, add it back to `requirements.in`.
3. **Run `docker build` once** on a machine that has Docker, to confirm the image builds and gunicorn starts.