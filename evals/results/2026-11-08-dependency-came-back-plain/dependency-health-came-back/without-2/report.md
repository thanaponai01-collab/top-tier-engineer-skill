`rich` is now a dependency and the 6 tests pass in a fresh Python 3.13 environment. Getting the lock file to work also moved two existing packages to newer versions, and I found a crash in the `render` command that was already there before my change.

**What I changed**
- **`requirements.in`:** added one line, `rich`. I didn't give it a minimum version, the same as `tzdata`.
- **`requirements.txt`:** regenerated from `requirements.in`. `pip-compile` isn't installed here, so I used `uv pip compile`, which does the same job. I put the header and line endings back the way they were. It kept your existing pins wherever it could. The diff is:
  - added `rich==15.0.0` and the three packages it needs: `markdown-it-py`, `mdurl` and `pygments`.
  - **`pyyaml` 5.3.1 → 6.0.3:** the old pin broke your own rule (`PyYAML>=6.0`).
  - **`urllib3` 1.24.1 → 2.8.0:** the installed `requests` (2.34.2) needs `urllib3>=1.26`.

  Nothing else changed. No code was touched.

**Things you should know**
1. **The old `requirements.txt` was already broken.** Because of those two bad pins, `pip install -r requirements.txt` couldn't succeed, so your Docker build would also have failed at that step. That's why two versions moved. The jump to `urllib3` 2.x is a major version, but the code doesn't import `urllib3` directly. It only reads YAML with `yaml.safe_load`, which works the same in PyYAML 6. 1.24.1 was also an old release with known security fixes missing.
2. **`python -m tripbook render trips/bangkok.yaml` crashes, and this has nothing to do with the dependencies.** It fails with `'dict object' has no attribute 'depart_dt'`. `templates/itinerary.html` uses `leg.depart_dt`, but nothing in the code ever creates that field. The tests don't cover rendering, which is why they still pass. I left it alone because you asked for no code changes, but it's worth a look.
3. When you refresh `requirements.txt` later, `pip-compile` as described in the README and `uv pip compile` give the same result.