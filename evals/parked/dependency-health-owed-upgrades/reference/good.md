**Short answer: the direct dependencies looked current, but the locked ones did not. I fixed four
things, kept two packages that looked unused, and one decision is yours.**

What I changed
- **urllib3 1.24.1 -> 1.26.20.** requirements.in never names it; requests pulls it in, and the
  lock pinned a version with several published security advisories (CVE-2019-11324, CVE-2020-26137,
  CVE-2023-45803 and more). Now on a fixed 1.26 release.
- **PyYAML 5.3.1 -> 6.0.2.** 5.3.1 has CVE-2020-14343 (code execution through full_load). The app
  only uses safe_load, but the hole was in the lock; requirements.in now asks for >=6.0.
- **click was missing from requirements.txt.** requirements.in asks for it and the CLI imports it,
  but the lock was never compiled after it was added, so a fresh install could not start the CLI.
  Pinned click 8.1.7.
- **simplejson removed.** Nothing imports it; rates.py uses the standard json module.
- **Docker base python:3.7-slim -> python:3.12-slim.** Python 3.7 is end of life since June 2023
  and gets no security fixes. The code uses zoneinfo and fromisoformat, which work on 3.12.

What I kept that looked unused
- **tzdata**: no file imports it, but zoneinfo needs it to find Asia/Bangkok on Windows and on
  slim images. Removing it breaks local times.
- **gunicorn**: no file imports it, but the Dockerfile CMD runs it to serve the web preview.

What you have to decide
- **Jinja2 stays on 2.11.3.** It has known holes (CVE-2024-22195 and later), but requirements.in
  says it is pinned on purpose: render.py uses @contextfilter, which Jinja2 3.1 removed. Moving
  needs render.py changed to pass_context and the itinerary rendered once to check it; the tests
  do not cover rendering. I left it rather than bump it past the code.

Tests: 6 of 6 pass before and after.
