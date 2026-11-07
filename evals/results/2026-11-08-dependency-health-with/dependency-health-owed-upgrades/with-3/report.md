The dependencies were in poor shape. They're fixed now: no serious problems are left, and the 6 tests passed before and after the changes. I didn't accept any risks on your behalf. This was the first check of this repo, so there was no earlier record to compare against.

**What I changed, worst first**
- **Docker image: Python 3.7 → 3.13.** Python 3.7 stopped getting security fixes in 2023. The old image was also already broken, because `tripbook/times.py` uses `zoneinfo`, which needs Python 3.9 or newer.
- **Jinja2 2.11.3 → 3.1.6.** The old version had four known security holes. It was pinned on purpose, because `render.py` used `@contextfilter`, which Jinja2 3.1 removed. I changed the code to `@pass_context`, the replacement, rather than keep the pin, and updated the comment in `requirements.in` to match.
- **PyYAML 5.3.1 → 6.0.3.** The old version had a known code-execution hole. The app only uses `safe_load`, which works the same way.
- **requests 2.32.4 → 2.34.2, plus three packages it pulls in:** urllib3 1.24.1 → 2.8.0 (a major version, with several holes), certifi → 2026.10.23 and idna → 3.20. All had known holes.
- **click was missing from `requirements.txt`.** Anyone installing from that file wouldn't get it, so the CLI wouldn't start. It's now included (8.5.1).
- **I rebuilt `requirements.txt` with `uv pip compile`.** pip-tools isn't installed on this machine, and uv produces the same kind of file. I didn't edit it by hand.

**What I removed**
- **simplejson:** nothing imports it. `rates.py` uses Python's built-in `json`.

**What I kept, though it looks unused**
- **gunicorn:** nothing imports it, but the Dockerfile runs it as the web server. It went from 23 to 26 (also major versions).
- **tzdata:** Python's time-zone code reads it on Windows and in slim Docker images. I added comments in `requirements.in` explaining why both stay.

**What the tests don't cover**
The 6 tests only cover the trip arithmetic, so I installed the new versions in a temporary environment and ran the other parts by hand. The template filter renders local times correctly, and the web app's function returns its page. I couldn't start gunicorn or build the Docker image here, because gunicorn doesn't run on Windows. The jumps to gunicorn 26 and urllib3 2.x are untested changes in behaviour, so please run `docker build` and `docker run` once.

**For you to decide**
- **`python -m tripbook render` crashes, and it did before my changes too.** The template asks each leg for a `depart_dt` field that no code ever sets, so you get `'dict object' has no attribute 'depart_dt'`. That's a code bug, not a dependency one, so I left it. The likely fix is to change the template to read `leg.depart`, or to add the field when the trip loads. Tell me which you prefer and I'll do it.
- **Python version:** I chose 3.13. If you'd rather stay on an older supported version, say so; the code needs at least 3.9.

The `.deps/` folder records this run, so leave it in place: the next check will compare against it.

<!-- file written by the agent: fixture/.deps/findings.md -->
# Dependency findings

Worst first. Each high one needs a fix or `--accept ID --reason ... --until ...`.

- [low] `used-without-import:gunicorn` gunicorn: not imported, but named in Dockerfile; check before removing
- [low] `used-without-import:tzdata` tzdata: not imported, but zoneinfo reads it where the OS has no time zone data (Windows, slim images); keep it

## Not checked
- nothing: every manifest found was checked
