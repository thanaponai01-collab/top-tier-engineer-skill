I fixed all eight serious dependency problems the check found, and all 6 tests still pass. I also found a bug in the `render` command that has nothing to do with dependencies, which you'll need to fix or decide about (point 1 below).

**What I changed, worst first**

- **Python version in the Docker image: 3.7 → 3.13.** Python 3.7 has had no security fixes since mid-2023. The image was also already broken: `tripbook/times.py` uses `zoneinfo`, which only exists from Python 3.9.
- **Jinja2 2.11.3 → 3.1.6** (plus MarkupSafe 1.1.1 → 3.0.4, which comes with it). The old version had four known security holes. It was pinned on purpose, because `render.py` used `@contextfilter`, which Jinja2 3.1 removed. Instead of keeping the pin, I changed the code to `@pass_context`, its direct replacement, and updated the comment in `requirements.in`. I checked by hand that the filter still converts the time zone correctly and still escapes HTML.
- **Security holes in the libraries `requests` uses:** urllib3 1.24.1 → 2.8.0 (four holes), certifi → 2026.10.23, idna → 3.20, and requests itself 2.32.4 → 2.34.2.
- **PyYAML 5.3.1 → 6.0.3.** It had a known hole, although your code uses the safe loader so it probably couldn't be reached. I also raised the minimum version in `requirements.in`.
- **click was missing from `requirements.txt`.** A Docker build or `pip install -r requirements.txt` would have left it out, so the command-line tool wouldn't start. It's now in the file.
- **Removed simplejson.** Nothing uses it; `rates.py` uses Python's built-in `json`.

I rebuilt `requirements.txt` from `requirements.in` with `uv`, because `pip-compile` isn't installed here. The file works the same way, and the README instructions still apply. I then installed it into a fresh environment and ran the tests there.

**What I left alone, and why**

- **gunicorn:** no code imports it, but the Dockerfile uses it to run the web preview.
- **tzdata:** no code imports it either, but `zoneinfo` needs it for time zone data on Windows and in slim Docker images.

**What you need to decide**

1. **`python -m tripbook render trips/bangkok.yaml` crashes.** The template uses `leg.depart_dt`, but nothing ever creates that field; the trip file only has `depart` as text. I ran it with the old Jinja2 as well and it crashes the same way, so it was already broken. I didn't fix it because it isn't a dependency problem. The likely fix is to turn `depart` into a date and time when the trip is loaded, or in the template. Do you want me to do it?
2. **gunicorn jumped from 23 to 26.** That's a big jump, and none of the tests touch it. The web app is a tiny plain one, so I expect no trouble, but run the Docker image once to make sure. I couldn't build or run Docker here.
3. **The tests only cover the trip calculations.** They don't touch Jinja2, YAML, requests or the command line, so "tests pass" doesn't prove those upgrades work. I checked the template filter by hand; the exchange-rate download (`rates`) wasn't tested at all.

The dependency check now reports no serious problems left and nothing it couldn't check. I left its record in `fixture/.deps/` so the next run can show what's new since today.

<!-- file written by the agent: fixture/.deps/findings.md -->
# Dependency findings

Worst first. Each high one needs a fix or `--accept ID --reason ... --until ...`.

- [low] `used-without-import:gunicorn` gunicorn: not imported, but named in Dockerfile; check before removing
- [low] `used-without-import:tzdata` tzdata: not imported, but zoneinfo reads it where the OS has no time zone data (Windows, slim images); keep it

## Not checked
- nothing: every manifest found was checked
