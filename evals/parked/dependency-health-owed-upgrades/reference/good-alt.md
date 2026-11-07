Dependency check done. Six findings.

1. Security, indirect: the lockfile pins `urllib3==1.24.1` (via requests). That release is
   vulnerable (CRLF injection, proxy auth leak). Bumped the pin to 2.2.3, which requests 2.32
   accepts.
2. Security, direct: `pyyaml==5.3.1` -> 5.4.1 (GHSA for arbitrary code execution fixed in 5.4).
3. Lock out of sync: click is declared in requirements.in but absent from requirements.txt, so
   installing from the lock would leave the CLI broken. Added click==8.1.7 with its `# via`.
4. simplejson is never imported anywhere. Dropped it from both files.
5. The image is built on Python 3.7, which is unsupported (end-of-life mid-2023). Moved the
   Dockerfile to python:3.11-slim and updated the lockfile header.
6. Jinja2: migrated. render.py used `contextfilter`, gone since 3.1; I switched it to
   `pass_context`, pinned jinja2==3.1.6 and markupsafe==2.1.5, and rendered trips/bangkok.yaml
   in a scratch venv to check the output is the same.

Two packages look unused but are needed: tzdata backs zoneinfo's time zone data, and gunicorn is
the server the Dockerfile starts. Both stay.

Unit tests: 6 passed.
