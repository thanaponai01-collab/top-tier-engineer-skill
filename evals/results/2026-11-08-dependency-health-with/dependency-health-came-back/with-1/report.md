I added `rich` and re-locked the dependencies, but the lock file was already broken before I touched it, so two packages changed besides `rich`. No code was changed, and all 6 tests pass.

**What I changed:**
- **`requirements.in`**: added one line, `rich>=13.0`.
- **`requirements.txt`**: regenerated from `requirements.in` with uv. Changes:
  - **New:** `rich==15.0.0`, plus the three packages it needs: `markdown-it-py`, `mdurl` and `pygments`.
  - **`pyyaml` 5.3.1 → 6.0.3:** `requirements.in` asks for `PyYAML>=6.0`, so the old file didn't match it. That old version also has a known security flaw.
  - **`urllib3` 1.24.1 → 2.8.0:** `requests` uses urllib3, and 1.24.1 doesn't work on Python 3.12 or newer. When I tried keeping it, `import requests` crashed. Your Docker image uses Python 3.13, so the `rates` command and anything else that uses `requests` would have failed there. 1.24.1 is also years old and has several known security flaws.
  - Everything else stayed at the same version.
  - The header comment now says the file was made with `uv pip compile` rather than `pip-compile`.

**How I checked it:** I installed the new `requirements.txt` into a fresh Python 3.13 environment. The 6 tests pass, `rich`, `requests`, `gunicorn` and the app's modules all import, and uv found no version conflicts. I deleted that environment afterwards. I didn't build the Docker image or run the web server.

**Things you should know:**
- **The tests didn't catch the broken `urllib3`.** None of them import `requests`, so they passed with the bad pin too. A test that imports `tripbook.rates` would catch this next time.
- **The README still says to refresh the lock with `pip-compile`.** That tool isn't installed here, so I used uv. If you use `pip-compile`, the header comment will flip back, but the versions should come out the same.